from typing import List
from fastapi import HTTPException
from app.schemas.video_lecture import VideoLecture, VideoLectureCreate, VideoLectureUpdate
from app.services import video_lecture_service
from uuid import UUID

async def list_lectures_handler(include_inactive: bool = False, token: str = None) -> List[dict]:
    """
    Controller handler to list video lectures.
    """
    try:
        return video_lecture_service.get_video_lectures(include_inactive=include_inactive, token=token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch video lectures: {str(e)}")

async def get_lecture_handler(lecture_id: UUID, include_inactive: bool = False, token: str = None) -> dict:
    """
    Controller handler to retrieve a single lecture by UUID.
    """
    try:
        lecture = video_lecture_service.get_video_lecture_by_id(lecture_id, include_inactive=include_inactive, token=token)
        if not lecture:
            raise HTTPException(status_code=404, detail="Video lecture not found")
        return lecture
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_lecture_handler(lecture_data: VideoLectureCreate, token: str = None) -> dict:
    """
    Controller handler to create a new video lecture.
    """
    try:
        return video_lecture_service.create_video_lecture(lecture_data, token=token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def update_lecture_handler(lecture_id: UUID, update_data: VideoLectureUpdate, token: str = None) -> dict:
    """
    Controller handler to update an existing video lecture.
    """
    try:
        return video_lecture_service.update_video_lecture(lecture_id, update_data, token=token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def delete_lecture_handler(lecture_id: UUID, token: str = None) -> dict:
    """
    Controller handler to soft-delete an existing video lecture.
    """
    try:
        video_lecture_service.soft_delete_video_lecture(lecture_id, token=token)
        return {"message": "Video lecture deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
