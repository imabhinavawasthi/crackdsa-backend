from typing import List, Optional
from app.database import get_supabase_client
from app.schemas.video_lecture import VideoLectureCreate, VideoLectureUpdate
from fastapi import HTTPException
from uuid import UUID

def get_video_lectures(include_inactive: bool = False, token: str = None) -> List[dict]:
    """
    Fetch video lectures from the database.
    If include_inactive is true, returns all lectures (admin use).
    Otherwise, returns only is_active=True.
    """
    client = get_supabase_client(jwt_token=token)
    query = client.table("video_lectures").select("*")
    
    if not include_inactive:
        query = query.eq("is_active", True)
        
    response = query.order("created_at", desc=True).execute()
    return response.data

def get_video_lecture_by_id(lecture_id: UUID, include_inactive: bool = False, token: str = None) -> Optional[dict]:
    """
    Fetch a single video lecture by its UUID.
    """
    client = get_supabase_client(jwt_token=token)
    query = client.table("video_lectures").select("*").eq("id", str(lecture_id))
    
    if not include_inactive:
        query = query.eq("is_active", True)
        
    response = query.limit(1).execute()
    return response.data[0] if response.data else None

def create_video_lecture(lecture_data: VideoLectureCreate, token: str = None) -> dict:
    """
    Inserts a new video lecture into the database.
    """
    client = get_supabase_client(jwt_token=token)
    
    response = client.table("video_lectures") \
        .insert(lecture_data.dict()) \
        .execute()
        
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create video lecture")
        
    return response.data[0]

def update_video_lecture(lecture_id: UUID, update_data: VideoLectureUpdate, token: str = None) -> dict:
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
        
    return response.data[0]

def soft_delete_video_lecture(lecture_id: UUID, token: str = None) -> bool:
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
        
    return True
