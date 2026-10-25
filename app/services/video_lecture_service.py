from typing import List, Optional, Dict, Any, Tuple
from app.database import get_supabase_client
from app.schemas.video_lecture import VideoLectureCreate, VideoLectureUpdate
from app.utils.crypto import encrypt_media_url
from app.utils.cache import cache_manager
from fastapi import HTTPException, status
from uuid import UUID
import time
import logging

logger = logging.getLogger(__name__)


def check_video_access(
    lecture: Dict[str, Any],
    user: Optional[Dict[str, Any]],
    client: Any,
    course_slug: Optional[str] = None,
    item_id: Optional[str] = None,
    courses_cache: Optional[List[Dict[str, Any]]] = None
) -> Tuple[bool, bool]:
    """
    Determines access for a video lecture.
    Returns: (has_access: bool, is_free: bool)

    Access rules:
    1. If explicitly configured as a free preview item in the course curriculum via item_id: Free preview access granted.
    2. If video itself has is_free=True on its attributes: Free access granted.
    3. If user has active Pro subscription or purchased the course containing the video: Paid access granted.
    4. Otherwise: Access denied (401 if unauthenticated, 403 if authenticated non-pro).
    """
    lecture_id = str(lecture.get("id"))
    attrs = lecture.get("attributes") or {}

    # 1. Direct free check on attributes if explicitly configured on the asset
    if attrs.get("is_free") is True or lecture.get("is_free") is True:
        return True, True

    # 2. Check if accessed via a specific free curriculum item
    if item_id:
        courses_data = courses_cache
        if courses_data is None:
            try:
                c_query = client.table("courses").select("id, slug, is_pro, curriculum")
                if course_slug:
                    c_query = c_query.eq("slug", course_slug)
                c_res = c_query.execute()
                courses_data = c_res.data or []
            except Exception as e:
                logger.error(f"Error fetching course for item_id check: {e}")
                courses_data = []

        for course in courses_data:
            for sec in (course.get("curriculum") or []):
                for itm in (sec.get("items") or []):
                    if str(itm.get("id") or "") == str(item_id) and str(itm.get("asset_id") or "") == lecture_id:
                        if bool(itm.get("is_free", False)):
                            return True, True
                for sub in (sec.get("subsections") or []):
                    for itm in (sub.get("items") or []):
                        if str(itm.get("id") or "") == str(item_id) and str(itm.get("asset_id") or "") == lecture_id:
                            if bool(itm.get("is_free", False)):
                                return True, True

    # 3. Not free. Admin has full access
    if user and "admin" in (user.get("roles") or []):
        return True, False

    # 4. If user not logged in, no access to paid content
    if not user:
        return False, False

    user_id = user.get("id")
    if not user_id:
        return False, False

    # 5. Check Pro subscription or individual course purchase
    try:
        now_epoch = int(time.time())
        u_res = client.table("users").select("pro_subscription, purchased_courses").eq("id", str(user_id)).execute()
        if u_res.data:
            db_user = u_res.data[0]
            pro_sub = db_user.get("pro_subscription") or {}

            # Check Pro subscription active
            if "subscription_active_till_epoch" in pro_sub:
                try:
                    expiry = int(pro_sub.get("subscription_active_till_epoch", 0))
                    if expiry == -1 or expiry > now_epoch:
                        return True, False
                except (ValueError, TypeError):
                    pass

            is_active = pro_sub.get("is_active", False)
            if (isinstance(is_active, str) and is_active.lower() == "true") or bool(is_active):
                return True, False

            # Check individual course purchase for courses containing this video
            pc = db_user.get("purchased_courses") or {}
            courses_arr = pc.get("courses", []) if isinstance(pc, dict) else (pc if isinstance(pc, list) else [])
            if courses_arr:
                courses_data = courses_cache
                if courses_data is None:
                    c_res = client.table("courses").select("id, slug, is_pro, curriculum").execute()
                    courses_data = c_res.data or []

                for course in courses_data:
                    contains_video = False
                    for sec in (course.get("curriculum") or []):
                        for itm in (sec.get("items") or []):
                            if itm.get("type") == "video" and str(itm.get("asset_id") or "") == lecture_id:
                                contains_video = True
                                break
                        if contains_video:
                            break
                        for sub in (sec.get("subsections") or []):
                            for itm in (sub.get("items") or []):
                                if itm.get("type") == "video" and str(itm.get("asset_id") or "") == lecture_id:
                                    contains_video = True
                                    break
                            if contains_video:
                                break

                    if contains_video:
                        cid = str(course.get("id"))
                        cslug = str(course.get("slug"))
                        for p in courses_arr:
                            if str(p.get("course_id") or "") in (cid, cslug):
                                valid_till = p.get("valid_till_epoch", -1)
                                if valid_till == -1 or valid_till > now_epoch:
                                    return True, False
    except Exception as e:
        logger.error(f"Error checking user entitlement for lecture {lecture_id}: {e}")

    return False, False


def get_video_lectures(
    include_inactive: bool = False,
    user: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None
) -> List[dict]:
    """
    Fetch video lectures from the database.
    - If include_inactive is true (admin audit), returns all lectures unmodified.
    - For public listing, redacts video_url for non-free videos if caller lacks Pro/enrollment.
    """
    user_id = user.get("id") if user else "anon"
    is_admin = bool(user and "admin" in (user.get("roles") or []))
    cache_key = f"videos:list:{include_inactive}:{is_admin}:{user_id if is_admin else 'public'}"
    cached_val = cache_manager.get(cache_key)
    if cached_val is not None:
        return cached_val

    client = get_supabase_client(jwt_token=token)
    query = client.table("video_lectures").select("*")

    if not include_inactive:
        query = query.eq("is_active", True)

    response = query.order("created_at", desc=True).execute()
    raw_lectures = response.data or []

    if include_inactive:
        return raw_lectures

    # Cache courses once for all lectures
    try:
        c_res = client.table("courses").select("id, slug, is_pro, curriculum").execute()
        courses_cache = c_res.data or []
    except Exception:
        courses_cache = []

    sanitized_lectures = []
    for lecture in raw_lectures:
        has_access, is_free = check_video_access(lecture, user, client, courses_cache=courses_cache)
        lecture_copy = dict(lecture)
        lecture_copy["is_free"] = is_free
        if not has_access:
            lecture_copy["video_url"] = None
            lecture_copy["resources"] = {}
            lecture_copy["is_locked"] = True
        else:
            lecture_copy["is_locked"] = False
            if lecture_copy.get("video_url"):
                lecture_copy["video_url"] = encrypt_media_url(lecture_copy["video_url"])
        sanitized_lectures.append(lecture_copy)

    cache_manager.set(cache_key, sanitized_lectures, ttl=86400, namespace="videos")
    return sanitized_lectures


def get_video_lecture_by_id(
    lecture_id: UUID,
    include_inactive: bool = False,
    course_slug: Optional[str] = None,
    item_id: Optional[str] = None,
    user: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None
) -> Optional[dict]:
    """
    Fetch a single video lecture by its UUID.
    Enforces access control:
    - Free lectures are open to all.
    - Paid lectures require an active Pro subscription or course purchase.
    """
    user_id = user.get("id") if user else "anon"
    is_admin = bool(user and "admin" in (user.get("roles") or []))
    cache_key = f"videos:detail:{lecture_id}:{course_slug}:{item_id}:{is_admin}:{user_id}"
    cached_val = cache_manager.get(cache_key)
    if cached_val is not None:
        return cached_val

    client = get_supabase_client(jwt_token=token)
    query = client.table("video_lectures").select("*").eq("id", str(lecture_id))

    if not include_inactive:
        query = query.eq("is_active", True)

    response = query.limit(1).execute()
    if not response.data:
        return None

    lecture = response.data[0]
    if include_inactive:
        return lecture

    has_access, is_free = check_video_access(
        lecture,
        user,
        client,
        course_slug=course_slug,
        item_id=item_id
    )
    lecture["is_free"] = is_free
    lecture["is_locked"] = not has_access

    if not has_access:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access this video lecture"
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Pro subscription or course enrollment required to access this video lecture"
        )

    if lecture.get("video_url"):
        lecture["video_url"] = encrypt_media_url(lecture["video_url"])

    cache_manager.set(cache_key, lecture, ttl=86400, namespace="videos")
    return lecture


def create_video_lecture(lecture_data: VideoLectureCreate, token: Optional[str] = None) -> dict:
    """
    Inserts a new video lecture into the database.
    """
    client = get_supabase_client(jwt_token=token)

    response = client.table("video_lectures") \
        .insert(lecture_data.dict()) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create video lecture")

    cache_manager.invalidate_namespace("videos")
    cache_manager.invalidate_namespace("courses")
    cache_manager.invalidate_namespace("live_classes")
    return response.data[0]


def update_video_lecture(lecture_id: UUID, update_data: VideoLectureUpdate, token: Optional[str] = None) -> dict:
    """
    Update an existing video lecture.
    Supports partial updates.
    """
    client = get_supabase_client(jwt_token=token)

    data = update_data.dict(exclude_unset=True)
    if not data:
        return get_video_lecture_by_id(lecture_id, include_inactive=True, token=token)

    data["updated_at"] = "now()"

    response = client.table("video_lectures") \
        .update(data) \
        .eq("id", str(lecture_id)) \
        .eq("is_active", True) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail=f"Video lecture with id {lecture_id} not found or inactive")

    cache_manager.invalidate_namespace("videos")
    cache_manager.invalidate_namespace("courses")
    cache_manager.invalidate_namespace("live_classes")
    return response.data[0]


def soft_delete_video_lecture(lecture_id: UUID, token: Optional[str] = None) -> bool:
    """
    Perform a soft delete by setting is_active to false.
    """
    client = get_supabase_client(jwt_token=token)

    response = client.table("video_lectures") \
        .update({"is_active": False}) \
        .eq("id", str(lecture_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail=f"Video lecture with id {lecture_id} not found")

    cache_manager.invalidate_namespace("videos")
    cache_manager.invalidate_namespace("courses")
    cache_manager.invalidate_namespace("live_classes")
    return True
