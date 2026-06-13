from typing import List
from pydantic import BaseModel, Field

from typing import Optional

class RoadmapItem(BaseModel):
    id: str = Field(..., description="Unique slug or ID of the asset (e.g. problem slug or video id) that exists in our DB")
    title: str
    type: str = Field(..., description="'video' | 'article' | 'problem'")
    difficulty: Optional[str] = Field(None, description="'Easy' | 'Medium' | 'Hard'")
    timeEstimate: str = Field("15 min", description="Time estimate (e.g., '15 min')")
    url: Optional[str] = None

class Topic(BaseModel):
    id: str
    title: str
    description: str
    items: List[RoadmapItem]
    icon: str = Field("Code2", description="Lucide icon name (e.g., Code2, BookOpen, Video)")
    iconColor: str = Field("text-blue-500", description="Tailwind text color class")
    iconBg: str = Field("bg-blue-50 dark:bg-blue-500/10", description="Tailwind background color class")

class Phase(BaseModel):
    id: str
    title: str
    subtitle: str
    color: str = Field("blue", description="'emerald' | 'blue' | 'purple'")
    topics: List[Topic]

class RoadmapStructure(BaseModel):
    phases: List[Phase]
