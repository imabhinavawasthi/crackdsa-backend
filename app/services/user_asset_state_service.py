from typing import List, Dict, Any, Optional
from app.database import get_supabase_client
from app.schemas.user_asset_state import (
    UserAssetStateResponseSchema,
    UserAssetStateUpdateSchema,
    UserActivitySummarySchema,
    UserBookmarkItemSchema,
    UserNoteItemSchema,
    UserProgressSummarySchema,
    ProblemDifficultyStatsSchema,
    AssetStatusEnum,
)
from uuid import UUID
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def is_valid_uuid(val: Any) -> bool:
    if not val:
        return False
    try:
        UUID(str(val))
        return True
    except (ValueError, AttributeError, TypeError):
        return False

class UserAssetStateService:
    """Service layer for User Asset States (Completion, Bookmarks, and Notes)"""

    TABLE_NAME = "user_asset_states"

    @staticmethod
    def get_user_asset_states(user_id: UUID, token: str) -> list[UserAssetStateResponseSchema]:
        """Fetch all learning interactions, bookmarks, and notepad entries for a user in a single bulk query"""
        try:
            client = get_supabase_client(token)
            
            response = client.table(UserAssetStateService.TABLE_NAME).select(
                "*"
            ).eq(
                "user_id", str(user_id)
            ).execute()
            
            states = []
            for item in response.data or []:
                states.append(UserAssetStateResponseSchema(**item))
                
            logger.info(f"Fetched {len(states)} asset state rows for user {user_id} in a single call")
            return states
        except Exception as e:
            logger.error(f"Error fetching asset states for user {user_id}: {str(e)}")
            raise

    @staticmethod
    def get_user_activity_summary(user_id: UUID, token: str) -> UserActivitySummarySchema:
        """
        Calculates user active streak metrics and current month active dates.
        Only fetches timestamps to minimize DB payload and processing overhead.
        """
        try:
            client = get_supabase_client(token)
            
            # Select timestamp columns and completion metadata needed for streaks and summary counts
            response = client.table(UserAssetStateService.TABLE_NAME).select(
                "updated_at, last_interacted_at, created_at, asset_type, asset_id, status"
            ).eq(
                "user_id", str(user_id)
            ).execute()
            
            dates_set = set()
            completed_lessons = 0
            cp_solved = 0

            for row in response.data or []:
                ts = row.get("updated_at") or row.get("last_interacted_at") or row.get("created_at")
                if ts and len(ts) >= 10:
                    dates_set.add(ts[:10])
                
                # Check completions
                if row.get("status") == "done":
                    a_type = row.get("asset_type")
                    a_id = str(row.get("asset_id") or "")
                    if a_type == "video":
                        completed_lessons += 1
                    if a_id.startswith("cp:"):
                        cp_solved += 1
            
            sorted_dates = sorted(list(dates_set))
            
            # Max / Best streak
            max_streak = 0
            running = 0
            prev_d = None
            for d_str in sorted_dates:
                try:
                    cur_d = datetime.strptime(d_str, "%Y-%m-%d").date()
                except Exception:
                    continue
                if prev_d is None:
                    running = 1
                else:
                    diff = (cur_d - prev_d).days
                    if diff == 1:
                        running += 1
                    elif diff > 1:
                        running = 1
                if running > max_streak:
                    max_streak = running
                prev_d = cur_d
                
            # Current streak counting backwards from today or yesterday
            today = datetime.utcnow().date()
            today_str = today.strftime("%Y-%m-%d")
            yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
            
            current_streak = 0
            rev_dates = list(reversed(sorted_dates))
            if rev_dates and (rev_dates[0] == today_str or rev_dates[0] == yesterday_str):
                current_streak = 1
                active_d = datetime.strptime(rev_dates[0], "%Y-%m-%d").date()
                for d_str in rev_dates[1:]:
                    try:
                        p_d = datetime.strptime(d_str, "%Y-%m-%d").date()
                    except Exception:
                        continue
                    if (active_d - p_d).days == 1:
                        current_streak += 1
                        active_d = p_d
                    else:
                        break
                        
            # Month active dates (current month, e.g. "2026-10")
            current_month_prefix = today.strftime("%Y-%m")
            month_active_dates = sorted([d for d in sorted_dates if d.startswith(current_month_prefix)])
            
            return UserActivitySummarySchema(
                current_streak=current_streak,
                max_streak=max_streak,
                current_month=current_month_prefix,
                month_active_dates=month_active_dates,
                month_active_count=len(month_active_dates),
                total_active_days=len(sorted_dates),
                completed_lessons_count=completed_lessons,
                cp_solved_count=cp_solved,
            )
        except Exception as e:
            logger.error(f"Error computing activity summary for user {user_id}: {str(e)}")
            raise

    @staticmethod
    def upsert_user_asset_state(
        user_id: UUID, 
        asset_id: str, 
        asset_type: str, 
        data: UserAssetStateUpdateSchema,
        token: str
    ) -> UserAssetStateResponseSchema:
        """
        Upsert (insert or merge-update) the state, notes, or bookmark of an individual asset for a user.
        Merges with existing states in the database to prevent accidental data loss!
        """
        try:
            client = get_supabase_client(token)
            user_uuid_str = str(user_id)

            # 1. Fetch existing state to perform a safe merge
            response = client.table(UserAssetStateService.TABLE_NAME).select(
                "*"
            ).eq(
                "user_id", user_uuid_str
            ).eq(
                "asset_id", asset_id
            ).eq(
                "asset_type", asset_type
            ).execute()

            existing_row = response.data[0] if response.data and len(response.data) > 0 else None

            # 2. Build payload by merging new changes over existing values
            payload = {
                "user_id": user_uuid_str,
                "asset_id": asset_id,
                "asset_type": asset_type,
                "updated_at": datetime.utcnow().isoformat(),
            }

            if existing_row:
                # Merge notes
                if data.notes is not None:
                    payload["notes"] = [note.dict() for note in data.notes]
                else:
                    payload["notes"] = existing_row.get("notes") or []

                # Merge bookmark flag
                if data.is_bookmarked is not None:
                    payload["is_bookmarked"] = data.is_bookmarked
                    if data.is_bookmarked and not existing_row.get("is_bookmarked"):
                        payload["bookmarked_at"] = datetime.utcnow().isoformat()
                    elif not data.is_bookmarked:
                        payload["bookmarked_at"] = None
                else:
                    payload["is_bookmarked"] = existing_row.get("is_bookmarked", False)
                    payload["bookmarked_at"] = existing_row.get("bookmarked_at")

                # Merge learning status
                if data.status is not None:
                    payload["status"] = data.status.value
                else:
                    payload["status"] = existing_row.get("status", "pending")

                # Merge metadata bucket
                if data.metadata is not None:
                    # Shallow merge metadata objects
                    current_meta = existing_row.get("metadata") or {}
                    current_meta.update(data.metadata)
                    payload["metadata"] = current_meta
                else:
                    payload["metadata"] = existing_row.get("metadata") or {}
                    
                payload["id"] = existing_row["id"]
                payload["last_interacted_at"] = datetime.utcnow().isoformat()
            else:
                # Initialize a brand-new row
                payload["notes"] = [note.dict() for note in data.notes] if data.notes is not None else []
                payload["is_bookmarked"] = data.is_bookmarked if data.is_bookmarked is not None else False
                payload["bookmarked_at"] = datetime.utcnow().isoformat() if payload["is_bookmarked"] else None
                payload["status"] = data.status.value if data.status is not None else "pending"
                payload["metadata"] = data.metadata or {}
                payload["last_interacted_at"] = datetime.utcnow().isoformat()

            # 3. Fire upsert to Supabase
            upsert_res = client.table(UserAssetStateService.TABLE_NAME).upsert(payload).execute()

            if not upsert_res.data or len(upsert_res.data) == 0:
                raise Exception("Failed to upsert asset state: No data returned from database")

            updated_row = upsert_res.data[0]
            logger.info(f"Upserted asset state {updated_row['id']} for user {user_id} on asset {asset_id}")
            return UserAssetStateResponseSchema(**updated_row)

        except Exception as e:
            logger.error(f"Error upserting asset state for user {user_id} on asset {asset_id}: {str(e)}")
            raise

    @staticmethod
    def _batch_resolve_assets(rows: List[Dict[str, Any]], client: Any) -> Dict[str, Dict[str, Any]]:
        """
        Efficiently batch resolve titles, links, and difficulty badges for assets in rows.
        Executes chunked batch lookups (max 50 IDs per query) to avoid URL limit issues.
        """
        problem_ids = set()
        video_ids = set()
        article_slugs = set()

        for r in rows:
            t = r.get("asset_type")
            aid = str(r.get("asset_id") or "").strip()
            if not aid:
                continue
            if t == "problem" and not aid.startswith("cp:"):
                problem_ids.add(aid)
            elif t == "video":
                video_ids.add(aid)
            elif t == "article":
                article_slugs.add(aid)

        problems_map = {}
        if problem_ids:
            p_uuids = [p for p in problem_ids if is_valid_uuid(p)]
            p_slugs = [p for p in problem_ids if not is_valid_uuid(p)]

            if p_uuids:
                for i in range(0, len(p_uuids), 50):
                    batch = p_uuids[i:i + 50]
                    try:
                        p_res = client.table("practice_problems").select("id, slug, title, difficulty").in_("id", batch).execute()
                        for p in p_res.data or []:
                            problems_map[str(p["id"])] = p
                            if p.get("slug"):
                                problems_map[p["slug"]] = p
                    except Exception as e:
                        logger.warning(f"Error querying practice_problems by id: {e}")

            if p_slugs:
                for i in range(0, len(p_slugs), 50):
                    batch = p_slugs[i:i + 50]
                    try:
                        p_res = client.table("practice_problems").select("id, slug, title, difficulty").in_("slug", batch).execute()
                        for p in p_res.data or []:
                            problems_map[str(p["id"])] = p
                            if p.get("slug"):
                                problems_map[p["slug"]] = p
                    except Exception as e:
                        logger.warning(f"Error querying practice_problems by slug: {e}")

        videos_map = {}
        if video_ids:
            v_uuids = [v for v in video_ids if is_valid_uuid(v)]
            v_slugs = [v for v in video_ids if not is_valid_uuid(v)]

            if v_uuids:
                for i in range(0, len(v_uuids), 50):
                    batch = v_uuids[i:i + 50]
                    try:
                        # video_lectures table has id, title, duration_seconds (NO slug column!)
                        v_res = client.table("video_lectures").select("id, title, duration_seconds").in_("id", batch).execute()
                        for v in v_res.data or []:
                            videos_map[str(v["id"])] = v
                    except Exception as e:
                        logger.warning(f"Error querying video_lectures by id: {e}")

            # Check live_classes table for any unresolved videos (both UUIDs and slugs)
            unresolved_v = [vid for vid in video_ids if vid not in videos_map]
            if unresolved_v:
                lc_uuids = [v for v in unresolved_v if is_valid_uuid(v)]
                lc_slugs = [v for v in unresolved_v if not is_valid_uuid(v)]

                if lc_uuids:
                    for i in range(0, len(lc_uuids), 50):
                        batch = lc_uuids[i:i + 50]
                        try:
                            lc_res = client.table("live_classes").select("id, class_url_slug, class_name, instructor_name").in_("id", batch).execute()
                            for lc in lc_res.data or []:
                                videos_map[str(lc["id"])] = {
                                    "id": lc["id"],
                                    "title": lc.get("class_name"),
                                    "slug": lc.get("class_url_slug"),
                                    "is_live_class": True,
                                    "instructor": lc.get("instructor_name")
                                }
                        except Exception as e:
                            logger.warning(f"Error querying live_classes by id: {e}")

                if lc_slugs:
                    for i in range(0, len(lc_slugs), 50):
                        batch = lc_slugs[i:i + 50]
                        try:
                            lc_res = client.table("live_classes").select("id, class_url_slug, class_name, instructor_name").in_("class_url_slug", batch).execute()
                            for lc in lc_res.data or []:
                                slug_key = lc.get("class_url_slug")
                                if slug_key:
                                    videos_map[slug_key] = {
                                        "id": lc["id"],
                                        "title": lc.get("class_name"),
                                        "slug": slug_key,
                                        "is_live_class": True,
                                        "instructor": lc.get("instructor_name")
                                    }
                        except Exception as e:
                            logger.warning(f"Error querying live_classes by slug: {e}")

        articles_map = {}
        if article_slugs:
            a_uuids = [a for a in article_slugs if is_valid_uuid(a)]
            a_slugs = [a for a in article_slugs if not is_valid_uuid(a)]

            if a_slugs:
                for i in range(0, len(a_slugs), 50):
                    batch = a_slugs[i:i + 50]
                    try:
                        a_res = client.table("articles").select("id, slug, title, read_time_minutes").in_("slug", batch).execute()
                        for a in a_res.data or []:
                            articles_map[a["slug"]] = a
                            articles_map[str(a["id"])] = a
                    except Exception as e:
                        logger.warning(f"Error querying articles by slug: {e}")

            if a_uuids:
                for i in range(0, len(a_uuids), 50):
                    batch = a_uuids[i:i + 50]
                    try:
                        a_res = client.table("articles").select("id, slug, title, read_time_minutes").in_("id", batch).execute()
                        for a in a_res.data or []:
                            articles_map[a["slug"]] = a
                            articles_map[str(a["id"])] = a
                    except Exception as e:
                        logger.warning(f"Error querying articles by id: {e}")

        return {
            "problems": problems_map,
            "videos": videos_map,
            "articles": articles_map,
        }

    @staticmethod
    def get_user_bookmarks(user_id: UUID, token: str) -> List[Dict[str, Any]]:
        """
        Returns all bookmarked items for a user with fully resolved titles,
        subtitles, links, difficulty labels, and badge colors in ONE unified call.
        """
        try:
            client = get_supabase_client(token)
            res = client.table(UserAssetStateService.TABLE_NAME).select(
                "*"
            ).eq(
                "user_id", str(user_id)
            ).eq(
                "is_bookmarked", True
            ).order(
                "updated_at", desc=True
            ).execute()

            rows = res.data or []
            if not rows:
                return []

            resolved = UserAssetStateService._batch_resolve_assets(rows, client)
            problems_map = resolved["problems"]
            videos_map = resolved["videos"]
            articles_map = resolved["articles"]

            results = []
            for r in rows:
                t = r.get("asset_type")
                aid = str(r.get("asset_id") or "").strip()
                meta = r.get("metadata") or {}
                notes_list = r.get("notes") or []

                item = {
                    "asset_id": aid,
                    "asset_type": t,
                    "status": r.get("status") or "pending",
                    "bookmarked_at": r.get("bookmarked_at") or r.get("updated_at"),
                    "updated_at": r.get("updated_at") or r.get("last_interacted_at"),
                    "notes_count": len(notes_list),
                    "metadata": meta,
                }

                if t == "problem":
                    if aid.startswith("cp:"):
                        title = meta.get("problem_name") or meta.get("title") or aid.replace("cp:", "")
                        rating = meta.get("difficulty_rating") or meta.get("rating")
                        item["title"] = title
                        item["subtitle"] = f"CP Sheet • {rating}" if rating else "CP Sheet Problem"
                        item["href"] = "/cp/newbie-to-expert"
                        item["badge"] = str(rating) if rating else "CP"
                        item["badge_color"] = "bg-blue-500/10 text-blue-500 border-blue-500/20"
                        item["difficulty"] = "Medium"
                    else:
                        prob = problems_map.get(aid)
                        title = prob.get("title") if prob else (meta.get("title") or "Practice Problem")
                        diff = prob.get("difficulty") if prob else "Medium"
                        slug = prob.get("slug") if prob else None
                        item["title"] = title
                        item["subtitle"] = diff
                        item["href"] = f"/problem/{slug}" if slug else "/practice"
                        item["badge"] = diff
                        item["difficulty"] = diff
                        if diff == "Easy":
                            item["badge_color"] = "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                        elif diff == "Hard":
                            item["badge_color"] = "bg-rose-500/10 text-rose-500 border-rose-500/20"
                        else:
                            item["badge_color"] = "bg-amber-500/10 text-amber-500 border-amber-500/20"
                elif t == "video":
                    vid = videos_map.get(aid)
                    if vid and vid.get("is_live_class"):
                        title = vid.get("title") or "Live Class"
                        item["title"] = title
                        item["subtitle"] = vid.get("instructor") or "Live Class"
                        slug = vid.get("slug")
                        item["href"] = f"/live-classes/{slug}" if slug else "/live-classes"
                        item["badge"] = "Live Class"
                        item["badge_color"] = "bg-blue-500/10 text-blue-500 border-blue-500/20"
                    else:
                        title = vid.get("title") if vid else (meta.get("title") or "Video Lecture")
                        dur_secs = vid.get("duration_seconds", 0) if vid else 0
                        mins = dur_secs // 60 if dur_secs else None
                        item["title"] = title
                        item["subtitle"] = f"{mins} min" if mins else "Video Lesson"
                        item["href"] = "/course/dsa"
                        item["badge"] = "Lesson"
                        item["badge_color"] = "bg-blue-500/10 text-blue-500 border-blue-500/20"
                elif t == "article":
                    art = articles_map.get(aid)
                    title = art.get("title") if art else (meta.get("title") or "CS Fundamental Article")
                    read_time = art.get("read_time_minutes") if art else 5
                    slug = art.get("slug") if art else aid
                    item["title"] = title
                    item["subtitle"] = f"{read_time} min read"
                    item["href"] = f"/cs-fundamentals/{slug}"
                    item["badge"] = "Article"
                    item["badge_color"] = "bg-purple-500/10 text-purple-500 border-purple-500/20"
                else:
                    item["title"] = aid
                    item["subtitle"] = "Resource"
                    item["href"] = "#"
                    item["badge"] = t
                    item["badge_color"] = "bg-gray-500/10 text-gray-500 border-gray-500/20"

                results.append(item)

            return results
        except Exception as e:
            logger.error(f"Error fetching bookmarks for user {user_id}: {str(e)}")
            raise

    @staticmethod
    def get_user_notes(user_id: UUID, token: str) -> List[Dict[str, Any]]:
        """
        Returns all flattened notes created by a user with fully resolved
        parent resource titles, links, and badge colors in ONE unified call.
        """
        try:
            client = get_supabase_client(token)
            res = client.table(UserAssetStateService.TABLE_NAME).select(
                "*"
            ).eq(
                "user_id", str(user_id)
            ).not_.is_(
                "notes", "null"
            ).order(
                "updated_at", desc=True
            ).execute()

            rows = [r for r in (res.data or []) if r.get("notes") and len(r.get("notes")) > 0]
            if not rows:
                return []

            resolved = UserAssetStateService._batch_resolve_assets(rows, client)
            problems_map = resolved["problems"]
            videos_map = resolved["videos"]
            articles_map = resolved["articles"]

            notes_list = []
            for r in rows:
                t = r.get("asset_type")
                aid = str(r.get("asset_id") or "").strip()
                meta = r.get("metadata") or {}

                if t == "problem":
                    if aid.startswith("cp:"):
                        title = meta.get("problem_name") or meta.get("title") or aid.replace("cp:", "")
                        rating = meta.get("difficulty_rating") or meta.get("rating")
                        subtitle = f"CP Sheet • {rating}" if rating else "CP Sheet"
                        href = "/cp/newbie-to-expert"
                        badge = str(rating) if rating else "CP"
                        badge_color = "bg-blue-500/10 text-blue-500 border-blue-500/20"
                    else:
                        prob = problems_map.get(aid)
                        title = prob.get("title") if prob else (meta.get("title") or "Practice Problem")
                        diff = prob.get("difficulty") if prob else "Medium"
                        slug = prob.get("slug") if prob else None
                        subtitle = diff
                        href = f"/problem/{slug}" if slug else "/practice"
                        badge = diff
                        if diff == "Easy":
                            badge_color = "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                        elif diff == "Hard":
                            badge_color = "bg-rose-500/10 text-rose-500 border-rose-500/20"
                        else:
                            badge_color = "bg-amber-500/10 text-amber-500 border-amber-500/20"
                elif t == "video":
                    vid = videos_map.get(aid)
                    if vid and vid.get("is_live_class"):
                        title = vid.get("title") or "Live Class"
                        subtitle = vid.get("instructor") or "Live Class"
                        slug = vid.get("slug")
                        href = f"/live-classes/{slug}" if slug else "/live-classes"
                        badge = "Live Class"
                        badge_color = "bg-blue-500/10 text-blue-500 border-blue-500/20"
                    else:
                        title = vid.get("title") if vid else (meta.get("title") or "Video Lecture")
                        subtitle = "Video Lesson"
                        href = "/course/dsa"
                        badge = "Lesson"
                        badge_color = "bg-blue-500/10 text-blue-500 border-blue-500/20"
                elif t == "article":
                    art = articles_map.get(aid)
                    title = art.get("title") if art else (meta.get("title") or "CS Fundamental Article")
                    read_time = art.get("read_time_minutes") if art else 5
                    slug = art.get("slug") if art else aid
                    subtitle = f"{read_time} min read"
                    href = f"/cs-fundamentals/{slug}"
                    badge = "Article"
                    badge_color = "bg-purple-500/10 text-purple-500 border-purple-500/20"
                else:
                    title = aid
                    subtitle = "Resource"
                    href = "#"
                    badge = t
                    badge_color = "bg-gray-500/10 text-gray-500 border-gray-500/20"

                for n in r.get("notes") or []:
                    notes_list.append({
                        "id": n.get("id"),
                        "text": n.get("text"),
                        "created_at": n.get("createdAt") or n.get("created_at") or r.get("updated_at") or "",
                        "asset_id": aid,
                        "asset_type": t,
                        "title": title,
                        "subtitle": subtitle,
                        "href": href,
                        "badge": badge,
                        "badge_color": badge_color,
                        "status": r.get("status") or "pending",
                    })

            notes_list.sort(key=lambda x: x.get("created_at") or "", reverse=True)
            return notes_list
        except Exception as e:
            logger.error(f"Error fetching notes for user {user_id}: {str(e)}")
            raise

    @staticmethod
    def get_user_progress_summary(user_id: UUID, token: str) -> Dict[str, Any]:
        """
        Computes all progress metrics, streaks, heatmap data, solved problem difficulty breakdown,
        and recent bookmarks/notes on the server.
        Completely eliminates the need for the frontend to fetch all practice problems.
        """
        try:
            client = get_supabase_client(token)

            # 1. Fetch user states
            res = client.table(UserAssetStateService.TABLE_NAME).select(
                "*"
            ).eq(
                "user_id", str(user_id)
            ).execute()
            rows = res.data or []

            # 2. Get active problems difficulty counts from DB
            prob_counts_res = client.table("practice_problems").select("difficulty").eq("is_active", True).execute()
            prob_rows = prob_counts_res.data or []
            total_prob_stats = {"total": len(prob_rows), "easy": 0, "medium": 0, "hard": 0}
            for pr in prob_rows:
                d = (pr.get("difficulty") or "Medium").capitalize()
                if d == "Easy":
                    total_prob_stats["easy"] += 1
                elif d == "Hard":
                    total_prob_stats["hard"] += 1
                else:
                    total_prob_stats["medium"] += 1

            # 3. Categorize user solved problems
            solved_problem_ids = set()
            articles_read = 0
            lectures_completed = 0
            bookmarked_count = 0
            interaction_dates = []

            for r in rows:
                t = r.get("asset_type")
                status_val = r.get("status")
                aid = str(r.get("asset_id") or "").strip()
                if r.get("is_bookmarked"):
                    bookmarked_count += 1

                ts = r.get("updated_at") or r.get("last_interacted_at")
                if ts:
                    interaction_dates.append(ts)

                if status_val == "done":
                    if t == "problem" and aid and not aid.startswith("cp:"):
                        solved_problem_ids.add(aid)
                    elif t == "video":
                        lectures_completed += 1
                    elif t == "article":
                        articles_read += 1

            # Resolve difficulty of solved problems
            solved_stats = {"total": len(solved_problem_ids), "easy": 0, "medium": 0, "hard": 0}
            if solved_problem_ids:
                s_list = list(solved_problem_ids)
                solved_diffs = {}

                s_uuids = [p for p in s_list if is_valid_uuid(p)]
                s_slugs = [p for p in s_list if not is_valid_uuid(p)]

                if s_uuids:
                    for i in range(0, len(s_uuids), 50):
                        batch = s_uuids[i:i + 50]
                        try:
                            p_res = client.table("practice_problems").select("id, slug, difficulty").in_("id", batch).execute()
                            for p in p_res.data or []:
                                diff = (p.get("difficulty") or "Medium").capitalize()
                                solved_diffs[str(p["id"])] = diff
                                if p.get("slug"):
                                    solved_diffs[p["slug"]] = diff
                        except Exception as e:
                            logger.warning(f"Error querying solved problems by id: {e}")

                unresolved_s = [pid for pid in s_list if pid not in solved_diffs]
                if unresolved_s:
                    for i in range(0, len(unresolved_s), 50):
                        batch = unresolved_s[i:i + 50]
                        try:
                            p_res = client.table("practice_problems").select("id, slug, difficulty").in_("slug", batch).execute()
                            for p in p_res.data or []:
                                diff = (p.get("difficulty") or "Medium").capitalize()
                                solved_diffs[str(p["id"])] = diff
                                if p.get("slug"):
                                    solved_diffs[p["slug"]] = diff
                        except Exception as e:
                            logger.warning(f"Error querying solved problems by slug: {e}")

                for pid in s_list:
                    d = solved_diffs.get(pid, "Medium")
                    if d == "Easy":
                        solved_stats["easy"] += 1
                    elif d == "Hard":
                        solved_stats["hard"] += 1
                    else:
                        solved_stats["medium"] += 1

            # 4. Activity Heatmap & Streaks
            heatmap_activity = {}
            for d_str in interaction_dates:
                if len(d_str) >= 10:
                    day_key = d_str[:10]
                    heatmap_activity[day_key] = heatmap_activity.get(day_key, 0) + 1

            # Compute streak
            activity_summary = UserAssetStateService.get_user_activity_summary(user_id, token)

            # 5. Top 3 recent bookmarks & notes
            all_bookmarks = UserAssetStateService.get_user_bookmarks(user_id, token)
            all_notes = UserAssetStateService.get_user_notes(user_id, token)

            return {
                "problems_solved": solved_stats,
                "total_problems": total_prob_stats,
                "articles_read": articles_read,
                "lectures_completed": lectures_completed,
                "bookmarked_count": bookmarked_count,
                "streak": activity_summary.current_streak,
                "recent_bookmarks": all_bookmarks[:3],
                "recent_notes": all_notes[:3],
                "heatmap_activity": heatmap_activity,
            }
        except Exception as e:
            logger.error(f"Error computing progress summary for user {user_id}: {str(e)}")
            raise
