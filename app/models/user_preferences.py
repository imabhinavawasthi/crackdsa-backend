from typing import List
from pydantic import BaseModel, Field

class UserPreferences(BaseModel):
    preparation_goal: str = Field(..., description="e.g. Interview Prep, Competitive Programming, Basics")
    target_companies: str = Field(..., description="e.g. FAANG, Product Based, Service Based, Startup")
    current_dsa_level: str = Field(..., description="e.g. Beginner, Intermediate, Advanced")
    timeline_days: int = Field(..., ge=7, le=180, description="Total days for preparation")
    hours_per_day: int = Field(..., ge=1, le=16, description="Hours available per day")
    preferred_language: str = Field(..., description="e.g. C++, Java, Python")
    strong_topics: List[str] = Field(..., description="Topics the user is already comfortable with")
    weak_topics: List[str] = Field(..., description="Topics the user struggles with and needs focus")

