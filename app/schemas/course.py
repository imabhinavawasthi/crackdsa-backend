from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from enum import Enum

class CourseCategoryEnum(str, Enum):
    INTERVIEW_PREP = "interview-prep"
    CORE_DSA = "core-dsa"
    SYSTEM_DESIGN = "system-design"
    SPECIALIZED = "specialized"

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

class CourseSectionItem(BaseModel):
    id: str
    title: str
    type: str  # "video" | "problem" | "article"
    asset_id: str  # UUID or Slug
    is_free: bool = False
    duration_label: Optional[str] = None

    class Config:
        from_attributes = True

class CourseSubsection(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    items: List[CourseSectionItem]

    class Config:
        from_attributes = True

class CourseSection(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    items: Optional[List[CourseSectionItem]] = None
    subsections: Optional[List[CourseSubsection]] = None

    class Config:
        from_attributes = True

class CourseMetadataSchema(BaseModel):
    difficulty: str = "Beginner"
    duration_weeks: int = 4
    total_projects: int = 0
    marketing_syllabus: List[str] = []
    thumbnail_url: Optional[str] = None
    prerequisites: List[str] = []
    learning_outcomes: List[str] = []
    rating: float = 5.0
    reviews: int = 0
    number_of_students: int = 0
    feedbacks: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True
        extra = "allow"  # Allow any other arbitrary fields

class CourseSummaryResponseSchema(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    category: CourseCategoryEnum
    instructors: List[InstructorSchema] = []
    instructor_ids: List[str] = []
    tags: List[str] = []
    is_pro: bool = True
    is_popular: bool = False
    status: CourseStatusEnum
    price: int
    original_price: int
    total_problems: int = 0
    total_articles: int = 0
    total_videos: int = 0
    metadata: CourseMetadataSchema = CourseMetadataSchema()

    class Config:
        from_attributes = True

class CourseResponseSchema(BaseModel):
    id: str                                             # UUID string
    slug: str                                           # SEO slug (e.g. 'dsa-bootcamp-recordings')
    title: str
    description: str
    category: CourseCategoryEnum
    
    # Support list of co-instructors
    instructors: List[InstructorSchema] = []
    instructor_ids: List[str] = []
    
    tags: List[str] = []
    is_pro: bool = True
    is_popular: bool = False
    status: CourseStatusEnum
    price: int
    original_price: int
    
    # Dynamic counts populated by backend at runtime
    total_problems: int = 0
    total_articles: int = 0
    total_videos: int = 0
    
    # Embedded detailed syllabus structure
    curriculum: List[CourseSection] = []
    
    # Extensible configuration bucket
    metadata: CourseMetadataSchema = CourseMetadataSchema()

    class Config:
        from_attributes = True

class CourseCreateSchema(BaseModel):
    slug: str                                           # SEO-friendly URL slug key
    title: str
    description: str
    category: CourseCategoryEnum
    id: Optional[str] = None                            # UUID string (optional, auto-generated)
    instructor_ids: List[str] = []                      # Array of instructor UUIDs
    tags: List[str] = []
    is_pro: bool = True
    is_popular: bool = False
    price: int
    original_price: int
    curriculum: List[CourseSection] = []
    status: CourseStatusEnum = CourseStatusEnum.DRAFT
    metadata: Optional[CourseMetadataSchema] = None

class CourseUpdateSchema(BaseModel):
    slug: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[CourseCategoryEnum] = None
    instructor_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_pro: Optional[bool] = None
    is_popular: Optional[bool] = None
    price: Optional[int] = None
    original_price: Optional[int] = None
    curriculum: Optional[List[CourseSection]] = None
    status: Optional[CourseStatusEnum] = None
    metadata: Optional[CourseMetadataSchema] = None


