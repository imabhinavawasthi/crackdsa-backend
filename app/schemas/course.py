from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class CourseCategoryEnum(str, Enum):
    INTERVIEW_PREP = "interview-prep"
    CORE_DSA = "core-dsa"
    SYSTEM_DESIGN = "system-design"
    ADVANCED = "advanced"

class CourseDifficultyEnum(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    ALL_LEVELS = "All Levels"

class CourseStatusEnum(str, Enum):
    ACTIVE = "active"
    UPCOMING = "upcoming"
    DRAFT = "draft"

class InstructorSchema(BaseModel):
    name: str
    role: str
    company: str
    color: str

    class Config:
        from_attributes = True

class CourseResponseSchema(BaseModel):
    id: str
    title: str
    description: str
    category: CourseCategoryEnum
    difficulty: CourseDifficultyEnum
    duration_weeks: int
    total_problems: int
    total_projects: int
    instructor: InstructorSchema
    tags: List[str]
    syllabus: List[str]
    is_pro: bool
    is_popular: bool
    status: CourseStatusEnum
    price: int
    original_price: int

    class Config:
        from_attributes = True
