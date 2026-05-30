from fastapi import APIRouter, HTTPException
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
        "original_price": 2999,
        "sections": [
            {
                "id": "section-1",
                "title": "Section 1: Language Basics, Big-O Analysis & Array Patterns",
                "description": "Foundations of programming languages, execution memory layout, complexity analysis, and warm-up array operations.",
                "items": [
                    {
                        "id": "item-1",
                        "title": "1.1 Language Basics & Memory Layout",
                        "type": "video",
                        "asset_id": "BasicsMemoryLayoutYouTubeId",
                        "is_free": True,
                        "duration_label": "24:15"
                    },
                    {
                        "id": "item-2",
                        "title": "1.2 Analysis of Algorithms & Big-O notation",
                        "type": "article",
                        "asset_id": "analysis-of-algorithms-big-o",
                        "is_free": True,
                        "duration_label": "8 min read"
                    },
                    {
                        "id": "item-3",
                        "title": "1.3 Reverse an Array",
                        "type": "problem",
                        "asset_id": "reverse-an-array",
                        "is_free": False,
                        "duration_label": "Easy"
                    },
                    {
                        "id": "item-4",
                        "title": "1.4 Find Minimum and Maximum in Array",
                        "type": "problem",
                        "asset_id": "find-min-max-array",
                        "is_free": False,
                        "duration_label": "Easy"
                    }
                ]
            },
            {
                "id": "section-2",
                "title": "Section 2: Core Patterns (Two Pointers & Sliding Window)",
                "description": "Master two of the most frequently asked linear scan patterns used in high-volume production interviews.",
                "subsections": [
                    {
                        "id": "subsection-2-1",
                        "title": "Subsection 2.1: Two Pointers Pattern",
                        "description": "Linear scans utilizing low and high boundary pointers.",
                        "items": [
                            {
                                "id": "item-5",
                                "title": "2.1 Two Pointers Pattern Deep-Dive",
                                "type": "video",
                                "asset_id": "TwoPointersPatternYouTubeId",
                                "is_free": False,
                                "duration_label": "42:10"
                            },
                            {
                                "id": "item-6",
                                "title": "2.2 Valid Palindrome",
                                "type": "problem",
                                "asset_id": "valid-palindrome",
                                "is_free": False,
                                "duration_label": "Easy"
                            }
                        ]
                    },
                    {
                        "id": "subsection-2-2",
                        "title": "Subsection 2.2: Sliding Window Pattern",
                        "description": "Subarray expansion and contraction optimization scans.",
                        "items": [
                            {
                                "id": "item-7",
                                "title": "2.3 Sliding Window Core Patterns & Guidelines",
                                "type": "article",
                                "asset_id": "sliding-window-guide",
                                "is_free": False,
                                "duration_label": "12 min read"
                            },
                            {
                                "id": "item-8",
                                "title": "2.4 Maximum Subarray (Kadane's Algorithm)",
                                "type": "problem",
                                "asset_id": "max-subarray",
                                "is_free": False,
                                "duration_label": "Medium"
                            }
                        ]
                    }
                ]
            },
            {
                "id": "section-3",
                "title": "Section 3: Advanced Structures (Binary Trees, Heaps & BSTs)",
                "description": "Understand tree-structured traversal patterns, breadth-first vs depth-first search, and heap priorities.",
                "items": [
                    {
                        "id": "item-9",
                        "title": "3.1 Binary Tree Traversals & Depth Strategies",
                        "type": "video",
                        "asset_id": "BinaryTreeStrategyYouTubeId",
                        "is_free": False,
                        "duration_label": "55:30"
                    },
                    {
                        "id": "item-10",
                        "title": "3.2 Maximum Depth of Binary Tree",
                        "type": "problem",
                        "asset_id": "max-depth-tree",
                        "is_free": False,
                        "duration_label": "Easy"
                    },
                    {
                        "id": "item-11",
                        "title": "3.3 Invert Binary Tree",
                        "type": "problem",
                        "asset_id": "invert-binary-tree",
                        "is_free": False,
                        "duration_label": "Easy"
                    }
                ]
            },
            {
                "id": "section-4",
                "title": "Section 4: Advanced Mastery (Dynamic Programming & Interview Prep)",
                "description": "Conquer dynamic programming by using memoization and tabulation. Finish with top strategic FAANG interview prep checklists.",
                "items": [
                    {
                        "id": "item-12",
                        "title": "4.1 Introduction to DP: Memoization vs Tabulation",
                        "type": "video",
                        "asset_id": "DPIntroductionYouTubeId",
                        "is_free": False,
                        "duration_label": "1:05:40"
                    },
                    {
                        "id": "item-13",
                        "title": "4.2 Climbing Stairs (DP)",
                        "type": "problem",
                        "asset_id": "climbing-stairs",
                        "is_free": False,
                        "duration_label": "Easy"
                    },
                    {
                        "id": "item-14",
                        "title": "4.3 Ultimate SDE Interview Prep Cheat Sheet",
                        "type": "article",
                        "asset_id": "sde-cheat-sheet",
                        "is_free": True,
                        "duration_label": "15 min read"
                    }
                ]
            }
        ]
    }
]

@router.get("/", response_model=List[CourseResponseSchema])
def list_courses():
    """
    Fetch all active SDE preparation courses from the CrackDSA Academy catalog.
    """
    return [course for course in COURSES_DATABASE if course["status"] == CourseStatusEnum.ACTIVE]

@router.get("/{course_id}", response_model=CourseResponseSchema)
def get_course(course_id: str):
    """
    Fetch a specific course by its unique ID, including detailed syllabus and sections.
    """
    for course in COURSES_DATABASE:
        if course["id"] == course_id and course["status"] == CourseStatusEnum.ACTIVE:
            return course
    raise HTTPException(status_code=404, detail="Course not found")

