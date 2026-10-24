from app.database import get_supabase_client
from app.utils.crypto import encrypt_media_url
from app.schemas.live_class import (
    LiveClassResponseSchema,
    LiveClassPaginatedResponse,
    LiveClassCounts,
)
from typing import List, Dict, Any, Optional
import time
import math
import logging

logger = logging.getLogger(__name__)

class LiveClassService:
    """Service layer for Live Classes database operations with pagination and visibility enforcement"""

    TABLE_NAME = "live-classes"

    @staticmethod
    def _hydrate_class_metadata(c: Dict[str, Any], now: int) -> LiveClassResponseSchema:
        start = int(c.get("class_time_epoch") or 0)
        duration_min = int(c.get("class_duration") or 60)
        duration_sec = duration_min * 60
        end = start + duration_sec

        # Dynamic status based strictly on time
        if start <= now <= end:
            status = "live"
        elif start > now:
            status = "upcoming"
        else:
            status = "completed"

        name = c.get("class_name") or "Live Class"
        instructor = c.get("instructor_name") or None
        subtopics = c.get("class_subtopics") or []
        topic = (c.get("class_topic") or "").strip().lower()

        # Derive thumbnail: direct field or YouTube video thumbnail
        thumbnail = c.get("thumbnail_url") or c.get("class_image") or None
        if not thumbnail and c.get("class_recording"):
            rec = str(c.get("class_recording"))
            import re
            yt_match = re.search(r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})', rec)
            if yt_match:
                thumbnail = f"https://img.youtube.com/vi/{yt_match.group(1)}/hqdefault.jpg"

        return LiveClassResponseSchema(
            id=str(c.get("id")),
            class_name=name,
            class_topic=topic if topic else None,
            instructor_name=instructor,
            class_time_epoch=start,
            class_duration=duration_min,
            class_link=c.get("class_link") or None,
            class_recording=c.get("class_recording") or None,
            class_notes=c.get("class_notes") or None,
            class_subtopics=subtopics,
            class_url_slug=c.get("class_url_slug") or "",
            status=status,
            visibility=c.get("visibility", "public"),
            thumbnail_url=thumbnail,
            class_image=c.get("class_image") or None,
            created_at=c.get("created_at"),
        )

    @classmethod
    def get_public_topics(cls) -> List[str]:
        """Fetch all unique topics present in public and free videos"""
        try:
            client = get_supabase_client()
            res = client.table(cls.TABLE_NAME).select("class_topic").in_("visibility", ["public", "free"]).execute()
            topics = set()
            for r in res.data or []:
                t = (r.get("class_topic") or "").strip().lower()
                if t:
                    topics.add(t)
            return sorted(list(topics))
        except Exception as e:
            logger.error(f"Error fetching public topics: {e}")
            return []

    @classmethod
    def list_live_classes(
        cls,
        status_filter: Optional[str] = "all",
        topic: Optional[str] = None,
        search: Optional[str] = None,
        visibility: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
        user: Optional[Dict[str, Any]] = None,
    ) -> LiveClassPaginatedResponse:
        """Fetch live classes with pagination, search, topic filter, and visibility enforcement"""
        client = get_supabase_client()

        # Build base query - fetch both public and free classes
        select_fields = "id, class_name, class_topic, instructor_name, class_time_epoch, class_duration, class_link, class_recording, class_notes, class_subtopics, class_url_slug, visibility, created_at"

        query = (
            client.table(cls.TABLE_NAME)
            .select(select_fields)
            .in_("visibility", ["public", "free"])
            .order("class_time_epoch", desc=True)
        )

        if topic and topic != "all":
            query = query.ilike("class_topic", f"%{topic}%")

        if search and search.strip():
            query = query.ilike("class_name", f"%{search.strip()}%")

        response = query.execute()
        raw_items = response.data or []
        now = int(time.time())

        # Hydrate records with real-time status
        all_hydrated = [cls._hydrate_class_metadata(item, now) for item in raw_items]

        # Calculate counts before status filtering
        live_count = sum(1 for c in all_hydrated if c.status == "live")
        upcoming_count = sum(1 for c in all_hydrated if c.status == "upcoming")
        completed_count = sum(1 for c in all_hydrated if c.status == "completed")
        free_count = sum(1 for c in all_hydrated if c.visibility == "free")

        counts = LiveClassCounts(
            all=len(all_hydrated),
            live=live_count,
            upcoming=upcoming_count,
            completed=completed_count,
            free=free_count,
        )

        # Check user's Pro status once for all items
        has_pro_access = cls._is_user_pro_or_admin(user, now)

        # Collect upcoming and live classes
        upcoming_classes = [
            cls._apply_pro_lock(c, has_pro_access)
            for c in all_hydrated
            if c.status in ("upcoming", "live")
        ]
        upcoming_classes.sort(key=lambda x: x.class_time_epoch or 0)

        # Get all topics present across public videos
        available_topics = cls.get_public_topics()

        # Apply status filter if specified
        filtered = all_hydrated
        if status_filter == "free" or visibility == "free":
            filtered = [c for c in all_hydrated if c.visibility == "free"]
        elif status_filter and status_filter != "all":
            filtered = [c for c in all_hydrated if c.status == status_filter]

        if visibility and visibility in ("public", "free"):
            filtered = [c for c in filtered if c.visibility == visibility]

        total_count = len(filtered)
        total_pages = max(1, math.ceil(total_count / limit)) if total_count > 0 else 1
        page_clamped = max(1, min(page, total_pages))

        # Paginate in memory to preserve dynamic status sorting
        start_idx = (page_clamped - 1) * limit
        end_idx = start_idx + limit
        paginated_raw = filtered[start_idx:end_idx]

        # Apply Pro access lock (redacting private recording, link, notes for non-pro on non-free classes)
        paginated_items = [cls._apply_pro_lock(c, has_pro_access) for c in paginated_raw]

        return LiveClassPaginatedResponse(
            items=paginated_items,
            total_count=total_count,
            page=page_clamped,
            limit=limit,
            total_pages=total_pages,
            counts=counts,
            available_topics=available_topics,
            upcoming_classes=upcoming_classes,
        )

    @classmethod
    def get_dashboard_featured_class(
        cls,
        user: Optional[Dict[str, Any]] = None
    ) -> Optional[LiveClassResponseSchema]:
        """
        Fetch single featured live class for dashboard:
        1. Ongoing live class if any, OR
        2. Most recent upcoming scheduled class if any (closest in future), OR
        3. Only 1 last class detail (most recent completed)
        Applies Pro verification: if non-pro and class is not free, sensitive links are redacted.
        """
        client = get_supabase_client()
        select_fields = "id, class_name, class_topic, instructor_name, class_time_epoch, class_duration, class_link, class_recording, class_notes, class_subtopics, class_url_slug, visibility, created_at"

        # Fetch all public & free classes
        response = (
            client.table(cls.TABLE_NAME)
            .select(select_fields)
            .in_("visibility", ["public", "free"])
            .order("class_time_epoch", desc=True)
            .execute()
        )
        raw_items = response.data or []
        if not raw_items:
            return None

        now = int(time.time())
        all_hydrated = [cls._hydrate_class_metadata(item, now) for item in raw_items]

        live_classes = [c for c in all_hydrated if c.status == "live"]
        upcoming_classes = [c for c in all_hydrated if c.status == "upcoming"]
        completed_classes = [c for c in all_hydrated if c.status == "completed"]

        # Sort upcoming by earliest first (closest upcoming class in future)
        upcoming_classes.sort(key=lambda x: x.class_time_epoch or 0)
        # Completed classes are already sorted desc by class_time_epoch

        chosen: Optional[LiveClassResponseSchema] = None
        if live_classes:
            chosen = live_classes[0]
        elif upcoming_classes:
            chosen = upcoming_classes[0]
        elif completed_classes:
            chosen = completed_classes[0]

        if not chosen:
            return None

        has_pro_access = cls._is_user_pro_or_admin(user, now)
        return cls._apply_pro_lock(chosen, has_pro_access)

    @classmethod
    def _is_user_pro_or_admin(cls, user: Optional[Dict[str, Any]], now: int) -> bool:
        """
        Check if user has an active Pro subscription or admin privileges.
        """
        if not user:
            return False
        roles = user.get("roles") or []
        if "admin" in roles:
            return True

        user_id = user.get("id")
        if not user_id:
            return False

        try:
            client = get_supabase_client()
            u_res = client.table("users").select("pro_subscription").eq("id", str(user_id)).execute()
            if u_res.data:
                db_user = u_res.data[0]
                pro_sub = db_user.get("pro_subscription") or {}
                if "subscription_active_till_epoch" in pro_sub:
                    try:
                        expiry = int(pro_sub.get("subscription_active_till_epoch", 0))
                        return (expiry == -1) or (expiry > now)
                    except (ValueError, TypeError):
                        pass
                is_active = pro_sub.get("is_active", False)
                if isinstance(is_active, str):
                    return is_active.lower() == "true"
                return bool(is_active)
        except Exception as e:
            logger.error(f"Error checking user pro subscription for live class: {e}")

        return False

    @classmethod
    def _apply_pro_lock(
        cls,
        c: LiveClassResponseSchema,
        has_pro_access: bool
    ) -> LiveClassResponseSchema:
        """
        Enforce Pro access control:
        If user has active Pro/admin OR class visibility is 'free', grant full access (is_locked=False).
        Otherwise mark is_locked=True and redact sensitive class_recording, class_link, and class_notes.
        """
        is_free = (c.visibility == "free")
        has_access = is_free or has_pro_access

        if not has_access:
            c.is_locked = True
            c.class_link = None
            c.class_recording = None
            c.class_notes = None
        else:
            c.is_locked = False
            if c.class_recording:
                c.class_recording = encrypt_media_url(c.class_recording)
            if c.class_link:
                c.class_link = encrypt_media_url(c.class_link)

        return c

    @classmethod
    def get_class_by_id_or_slug(
        cls,
        id_or_slug: str,
        user: Optional[Dict[str, Any]] = None
    ) -> Optional[LiveClassResponseSchema]:
        """Fetch single live class by UUID or slug without any mock data"""
        client = get_supabase_client()
        from uuid import UUID
        is_uuid = False
        try:
            UUID(id_or_slug)
            is_uuid = True
        except ValueError:
            is_uuid = False

        query = client.table(cls.TABLE_NAME).select("*")
        if is_uuid:
            res = query.eq("id", id_or_slug).execute()
        else:
            res = query.eq("class_url_slug", id_or_slug).execute()

        if not res.data:
            return None

        now = int(time.time())
        hydrated = cls._hydrate_class_metadata(res.data[0], now)
        has_pro_access = cls._is_user_pro_or_admin(user, now)
        return cls._apply_pro_lock(hydrated, has_pro_access)
