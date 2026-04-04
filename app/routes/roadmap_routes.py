from fastapi import APIRouter, Depends
from typing import Optional
from app.models.user_preferences import UserPreferences
from app.models.roadmap import RoadmapResponse
from app.controllers.roadmap_controller import generate_roadmap_handler
from app.dependencies import get_token

router = APIRouter(
    prefix="/roadmap",
    tags=["Roadmap Generation"]
)

@router.post("/generate", response_model=RoadmapResponse)
async def generate_roadmap_endpoint(prefs: UserPreferences, token: Optional[str] = Depends(get_token)):
    """
    Endpoint to trigger generation of an AI-assisted roadmap.
    Receives JSON user preferences and returns a roadmap configuration.
    """
    return await generate_roadmap_handler(prefs, token=token)
