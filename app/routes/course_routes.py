from fastapi import APIRouter
from typing import List
from app.schemas.course import CourseResponseSchema, CourseCategoryEnum, CourseDifficultyEnum, CourseStatusEnum

router = APIRouter(
    prefix="/courses",
    tags=["Courses"]
)

# Database with only the single high-value sellable premium course
COURSES_DATABASE = [
    {
        "id": "dsa-bootcamp-recordings",
        "title": "Ultimate DSA Revision: 3-Month Live Bootcamp recordings",
        "description": "Get lifetime access to the complete recordings of our exclusive 3-month Live DSA Bootcamp. Covers the entire DSA syllabus across 50 intensive interactive sessions, curated topic coding sheets, and conceptual SDE revision articles.",
        "category": CourseCategoryEnum.CORE_DSA,
        "difficulty": CourseDifficultyEnum.ALL_LEVELS,
        "duration_weeks": 12,
        "total_problems": 150,
        "total_projects": 0,
        "instructor": {
            "name": "Abhinav Awasthi",
            "role": "Founder, CrackDSA",
            "company": "Ex-Google SDE",
            "color": "from-brand-500 to-blue-light-400"
        },
        "tags": ["50+ Recordings", "Entire Syllabus", "SDE Revision Articles", "Lifetime Access"],
        "syllabus": [
            "Session 1-10: Language Basics, Big-O Analysis & Array Patterns",
            "Session 11-25: Core Patterns (Two Pointers, Sliding Window, Lists & Stacks)",
            "Session 26-40: Advanced Structures (Binary Trees, Heaps, BSTs & Sorting)",
            "Session 41-50: Advanced Mastery (Dynamic Programming, Graph DFS/BFS & Interview Prep)"
        ],
        "is_pro": True,
        "is_popular": True,
        "status": CourseStatusEnum.ACTIVE,
        "price": 999,
        "original_price": 2999
    }
]

@router.get("/", response_model=List[CourseResponseSchema])
def list_courses():
    """
    Fetch all active SDE preparation courses from the CrackDSA Academy catalog.
    """
    return [course for course in COURSES_DATABASE if course["status"] == CourseStatusEnum.ACTIVE]
