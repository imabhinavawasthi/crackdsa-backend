from typing import List
from pydantic import BaseModel, Field

class ProblemTask(BaseModel):
    slug: str
    title: str
    difficulty: str
    difficulty_level: int
    pattern: str
    importance_score: float
    frequency_score: float

class DayPlan(BaseModel):
    day: int
    focus_topic: str
    learning_objective: str
    tasks: List[ProblemTask]
    revision_topics: List[str]

class RoadmapResponse(BaseModel):
    total_days: int
    target_company_level: str
    days: List[DayPlan]

