from fastapi import HTTPException
from typing import Optional, List, Dict, Any
from app.models.user_preferences import RoadmapUserInput
from app.services.roadmap_service import (
    generate_and_save_roadmap,
    list_user_roadmaps,
    get_active_roadmap,
    get_roadmap_by_id,
    activate_roadmap,
    rename_roadmap,
    delete_roadmap
)

async def generate_roadmap_handler(user_id: str, prefs: RoadmapUserInput, token: str) -> dict:
    try:
        return await generate_and_save_roadmap(user_id, prefs, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate roadmap: " + str(e))

def list_roadmaps_handler(user_id: str, token: str) -> List[Dict[str, Any]]:
    try:
        return list_user_roadmaps(user_id, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list roadmaps: " + str(e))

def get_active_roadmap_handler(user_id: str, token: str) -> Optional[Dict[str, Any]]:
    try:
        return get_active_roadmap(user_id, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get active roadmap: " + str(e))

def get_roadmap_by_id_handler(user_id: str, roadmap_id: str, token: str) -> Optional[Dict[str, Any]]:
    try:
        roadmap = get_roadmap_by_id(user_id, roadmap_id, token)
        if not roadmap:
            raise HTTPException(status_code=404, detail="Roadmap not found")
        return roadmap
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get roadmap by id: " + str(e))

def activate_roadmap_handler(user_id: str, roadmap_id: str, token: str) -> dict:
    try:
        return activate_roadmap(user_id, roadmap_id, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to activate roadmap: " + str(e))

def rename_roadmap_handler(user_id: str, roadmap_id: str, new_title: str, token: str) -> dict:
    try:
        return rename_roadmap(user_id, roadmap_id, new_title, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to rename roadmap: " + str(e))

def delete_roadmap_handler(user_id: str, roadmap_id: str, token: str) -> dict:
    try:
        return delete_roadmap(user_id, roadmap_id, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete roadmap: " + str(e))
