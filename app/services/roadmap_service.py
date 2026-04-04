from typing import Optional
from app.models.user_preferences import UserPreferences
from app.models.roadmap import RoadmapResponse
from app.utils.validators import validate_preferences
from app.utils.problem_loader import get_relevant_problems_for_ai
from app.services.ai_service import generate_roadmap_from_ai

async def create_roadmap(prefs: UserPreferences, token: Optional[str] = None) -> RoadmapResponse:
    """
    Orchestrates the roadmap generation process.
    Supports JWT token for user-specific context.
    """
    # 1. Additional domain validation
    validate_preferences(prefs)
    
    # 2. Get data (currently local file-based, but token-ready)
    problems = get_relevant_problems_for_ai(
        strong_topics=prefs.strong_topics, 
        weak_topics=prefs.weak_topics
    )
    
    # 3. Call AI to structure this
    roadmap = await generate_roadmap_from_ai(prefs=prefs, problems=problems)
    
    # 4. Return formatted validated response
    return roadmap
