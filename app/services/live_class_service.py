from app.database import get_supabase_client
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
        """Fetch all unique topics present in public videos"""
        try:
            client = get_supabase_client()
            res = client.table(cls.TABLE_NAME).select("class_topic").eq("visibility", "public").execute()
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
        page: int = 1,
        limit: int = 10,
    ) -> LiveClassPaginatedResponse:
        """Fetch live classes with pagination, search, topic filter, and visibility enforcement"""
        client = get_supabase_client()

        # Build base query - strictly fetch only public classes
        select_fields = "id, class_name, class_topic, instructor_name, class_time_epoch, class_duration, class_link, class_recording, class_notes, class_subtopics, class_url_slug, visibility, created_at"

        query = (
            client.table(cls.TABLE_NAME)
            .select(select_fields)
            .eq("visibility", "public")
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

        counts = LiveClassCounts(
            all=len(all_hydrated),
            live=live_count,
            upcoming=upcoming_count,
            completed=completed_count,
        )

        # Collect upcoming and live classes
        upcoming_classes = [c for c in all_hydrated if c.status in ("upcoming", "live")]
        upcoming_classes.sort(key=lambda x: x.class_time_epoch or 0)

        # Get all topics present across public videos
        available_topics = cls.get_public_topics()

        # Apply status filter if specified
        filtered = all_hydrated
        if status_filter and status_filter != "all":
            filtered = [c for c in all_hydrated if c.status == status_filter]

        total_count = len(filtered)
        total_pages = max(1, math.ceil(total_count / limit)) if total_count > 0 else 1
        page_clamped = max(1, min(page, total_pages))

        # Paginate in memory to preserve dynamic status sorting
        start_idx = (page_clamped - 1) * limit
        end_idx = start_idx + limit
        paginated_items = filtered[start_idx:end_idx]

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
    def get_class_by_id_or_slug(cls, id_or_slug: str) -> Optional[LiveClassResponseSchema]:
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
        return cls._hydrate_class_metadata(res.data[0], now)
