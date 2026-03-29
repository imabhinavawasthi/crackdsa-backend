from app.models.user_preferences import UserPreferences
from app.models.roadmap import RoadmapResponse
from app.utils.validators import validate_preferences
from app.utils.problem_loader import get_relevant_problems_for_ai
from app.services.ai_service import generate_roadmap_from_ai

async def create_roadmap(prefs: UserPreferences) -> RoadmapResponse:
    """
    Orchestrates the roadmap generation process:
    1. Validates input additionally if needed
    2. Loads problem subset
    3. Calls AI logic
    4. Returns finalized response
    """
    # 1. Additional domain validation (beyond Pydantic types)
    validate_preferences(prefs)
    
    # 2. Get data
    problems = get_relevant_problems_for_ai(
        strong_topics=prefs.strong_topics, 
        weak_topics=prefs.weak_topics
    )
    
    # 3. Call AI to structure this
    roadmap = await generate_roadmap_from_ai(prefs=prefs, problems=problems)
    
    # 4. Return formatted validated response
    return roadmap
