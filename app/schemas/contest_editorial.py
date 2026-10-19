from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class ContestEditorialProblem(BaseModel):
    id: str
    platform: str
    created_at: str
    problem_name: str
    problem_description: Optional[str] = None
    problem_link: Optional[str] = None
    video_editorial: Optional[str] = None
    editorial: Optional[str] = None
    difficulty: Optional[int] = 0
    company_tags: Optional[Any] = None
    topic_tags: Optional[Any] = None
    slug_url: str
    contest: Optional[str] = None
    solution_link: Optional[str] = None
    problem_index: Optional[str] = None
    difficulty_label: Optional[str] = "Medium"
    has_editorial: bool = False

class ContestSummary(BaseModel):
    id: str
    platform: str
    contest: str
    date: str
    created_at: str
    total_problems: int
    easy_count: int
    medium_count: int
    hard_count: int
    has_video: bool
    badge: Optional[str] = None

class ContestDetail(BaseModel):
    id: str
    platform: str
    contest: str
    date: str
    total_problems: int
    contest_url: Optional[str] = None
    problems: List[ContestEditorialProblem] = []

class ContestSuggestionCreate(BaseModel):
    platform: str
    contest_name: str
    contest_url: Optional[str] = None
    notes: Optional[str] = None
