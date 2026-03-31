"""AI service using Google Gemini."""

import json
import google.generativeai as genai
from typing import List, Dict, Any
from app.config import settings
from app.models.user_preferences import UserPreferences
from app.models.roadmap import RoadmapResponse

# Initialize Gemini SDK
genai.configure(api_key=settings.GEMINI_API_KEY)


async def generate_roadmap_from_ai(prefs: UserPreferences, problems: List[Dict[str, Any]]) -> RoadmapResponse:
    """
    Sends the user preferences and available problems to Gemini to generate a structured roadmap.
    Uses Gemini's built-in structured output support with the Pydantic RoadmapResponse schema.
    """
    
    system_prompt = (
        "You are an expert personalized Data Structures and Algorithms (DSA) instructor. "
        "Your task is to generate a day-wise study roadmap based on the user's preferences and a provided list of problems. "
        "Rules:\n"
        "1. Distribute the provided problems logically across the timeline.\n"
        "2. Include a revision day every 7th day (no new problems that day, just add revision topics).\n"
        "3. Prioritize 'weak_topics' more frequently, and build confidence with 'strong_topics'.\n"
        "4. Start with easier problems and gradually increase difficulty.\n"
        "5. Output must strictly follow the required JSON output schema."
    )
    
    user_prompt = f"""
User Preferences:
- Preparation Goal: {prefs.preparation_goal}
- Target Companies: {prefs.target_companies}
- Current DSA Level: {prefs.current_dsa_level}
- Timeline: {prefs.timeline_days} days
- Hours Per Day: {prefs.hours_per_day} hours
- Preferred Language: {prefs.preferred_language}
- Strong Topics: {', '.join(prefs.strong_topics) if prefs.strong_topics else 'None specified'}
- Weak Topics: {', '.join(prefs.weak_topics) if prefs.weak_topics else 'None specified'}

Available Problems from our Dataset:
{json.dumps(problems, indent=2)}

Please generate a highly personalized, structured {prefs.timeline_days}-day roadmap using these available problems.
"""

    prompt_content = f"{system_prompt}\n\n{user_prompt}"
    
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    response = await model.generate_content_async(
        prompt_content,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=RoadmapResponse
        )
    )
    
    # Parse the text (which is guaranteed to match the Pydantic schema) into the Pydantic object
    parsed_roadmap = RoadmapResponse.model_validate_json(response.text)
    return parsed_roadmap


