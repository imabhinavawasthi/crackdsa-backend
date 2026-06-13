from typing import List, Optional
from pydantic import BaseModel, Field

class RoadmapUserInput(BaseModel):
    # Goal & Preparation
    primary_goal: str = Field(..., description="Primary goal (e.g. Internship, Placement, Job Switch, Promotion, Competitive Programming)")
    target_role: str = Field(..., description="Role preparing for (e.g., Software Engineer, Frontend Developer, Backend Developer)")
    target_company_tier: str = Field(..., description="Target company tier (e.g. Tier 1 (FAANG), Tier 2 Product Companies, Tier 3 Companies, Service-Based Companies)")
    urgency_level: str = Field(..., description="Urgency level (Casual, Serious, Critical)")
    duration_weeks: int = Field(..., description="Total preparation duration in weeks")
    
    # Current DSA Experience
    experience_level: str = Field(..., description="Current DSA experience level (Beginner, Intermediate, Advanced)")
    problems_solved_count: int = Field(..., description="Approximate number of DSA problems solved")
    
    # Topic-Level Understanding
    strong_topics: List[str] = Field(default_factory=list, description="Topics the user is already comfortable with")
    weak_topics: List[str] = Field(default_factory=list, description="Topics the user needs more practice and guidance")
    
    # Time Availability
    time_per_week_hours: int = Field(..., description="Number of hours available per week for preparation")
    
    # Learning Preferences
    learning_style: str = Field(..., description="Learning style (Theory First, Problems First, Balanced)")
    
    # Programming Preference
    programming_language: str = Field(..., description="Preferred programming language (C++, Java, Python, JavaScript, Other)")
    
    # Backward compatibility
    preferred_language: Optional[str] = Field(default="Any", description="Preferred programming language (backward compatibility)")
