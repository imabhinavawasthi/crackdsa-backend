"""AI service using Google Gemini."""

import json
import google.generativeai as genai
from typing import List, Dict, Any
from app.config import settings
from app.models.user_preferences import RoadmapUserInput
from app.models.roadmap import RoadmapStructure

# Initialize Gemini SDK
genai.configure(api_key=settings.GEMINI_API_KEY)


async def generate_roadmap_from_ai(prefs: RoadmapUserInput, problems: List[Dict[str, Any]]) -> RoadmapStructure:
    """
    Sends the user preferences and available problems to Gemini to generate a structured roadmap.
    Uses Gemini's built-in structured output support with the Pydantic RoadmapStructure schema.
    """
    
    system_prompt = (
        "You are an expert personalized Data Structures and Algorithms (DSA) instructor. "
        "Your task is to generate a comprehensive study roadmap structured into logical Phases, Topics, and Items "
        "based on the user's preferences, available preparation time, and a provided list of problems.\n\n"
        "Rules:\n"
        "1. Create logical macro-phases (e.g. 'Phase 1: Foundation', 'Phase 2: Core Patterns').\n"
        "2. Break down phases into core topics (e.g. 'Arrays & Hashing', 'Two Pointers').\n"
        "3. For each topic, assign relevant problems from the provided database. Give them type='problem'.\n"
        "4. Include mock 'video' and 'article' items to introduce topics before solving problems.\n"
        "5. Prioritize 'weak_topics' heavily, and build confidence with 'strong_topics'.\n"
        "6. Align the density of the plan to the user's `duration_weeks` and `time_per_week_hours`.\n"
        "7. Ensure the generated roadmap strictly adheres to the required JSON output schema.\n"
        "8. Personalization guidelines:\n"
        "   - Learning Style:\n"
        "     * 'Theory First': Include more introductory videos and concept articles before coding problems.\n"
        "     * 'Problems First': Keep video/article items to a minimum; jump straight into problems.\n"
        "     * 'Balanced': Provide a steady mix of theory and coding practice.\n"
        "   - Primary Goal:\n"
        "     * 'Competitive Programming': Focus on advanced graph/tree algorithms, math, number theory, and recursion.\n"
        "     * 'Job Switch' / 'Placement' / 'Internship': Emphasize high-frequency interview patterns and FAANG-specific problems.\n"
        "     * 'Promotion': Focus on system design foundations and algorithmic optimizations.\n"
        "   - Urgency Level:\n"
        "     * 'Critical': Streamline the plan to cover ONLY the absolute highest-yield topics (DP, Graphs, Trees, Arrays).\n"
        "     * 'Casual': Give a broad overview with comfortable conceptual coverage.\n"
        "   - Experience Level & Solved Count:\n"
        "     * 'Beginner' or low solved count: Start with fundamental basics (Space/Time complexity, Basic Arrays, Recursion).\n"
        "     * 'Advanced' or high solved count: Skip introductory basics and jump straight to advanced tree/graph patterns and DP.\n"
        "   - Programming Language: Customize item descriptions or references to the user's preferred language."
    )
    
    user_prompt = f"""
User Profile & Preferences:
- Primary Goal: {prefs.primary_goal}
- Target Role: {prefs.target_role}
- Target Company Tier: {prefs.target_company_tier}
- Urgency Level: {prefs.urgency_level}
- Duration Available: {prefs.duration_weeks} weeks
- Time Commitment: {prefs.time_per_week_hours} hours/week
- Current DSA Experience: {prefs.experience_level}
- Problems Solved Count: {prefs.problems_solved_count} solved
- Learning Style: {prefs.learning_style}
- Programming Language Preference: {prefs.programming_language}
- Strong Topics: {', '.join(prefs.strong_topics) if prefs.strong_topics else 'None specified'}
- Weak Topics: {', '.join(prefs.weak_topics) if prefs.weak_topics else 'None specified'}

Available Problems from our Dataset:
{json.dumps(problems, indent=2)}

Please generate a highly personalized, structured roadmap utilizing the problems provided according to the personalization guidelines.
"""

    prompt_content = f"{system_prompt}\n\n{user_prompt}"
    
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    response = await model.generate_content_async(
        prompt_content,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=RoadmapStructure
        )
    )
    
    parsed_roadmap = RoadmapStructure.model_validate_json(response.text)
    return parsed_roadmap

