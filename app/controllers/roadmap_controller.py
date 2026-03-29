from fastapi import HTTPException
from app.models.user_preferences import UserPreferences
from app.models.roadmap import RoadmapResponse
from app.services.roadmap_service import create_roadmap

async def generate_roadmap_handler(prefs: UserPreferences) -> RoadmapResponse:
    """
    Controller logic to handle generating a roadmap.
    It catches domain exceptions and converts them to HTTP errors.
    """
    try:
        return await create_roadmap(prefs)
    except ValueError as e:
        # Client input errors from validation
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Internal server errors (e.g. LLM failure)
        # In production we'd log this properly
        raise HTTPException(status_code=500, detail="Failed to generate roadmap: " + str(e))
