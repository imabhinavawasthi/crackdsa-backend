from app.database import get_supabase_client
from app.schemas.course import (
    CourseCreateSchema,
    CourseUpdateSchema,
    CourseResponseSchema,
    CourseSummaryResponseSchema,
    CourseSection,
    InstructorSchema,
)
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CourseService:
    """Service layer for Course database and curriculum operations"""

    COURSES_TABLE = "courses"
    INSTRUCTORS_TABLE = "instructors"
    VIDEOS_TABLE = "video_lectures"
    PROBLEMS_TABLE = "practice_problems"
    ARTICLES_TABLE = "articles"

    @staticmethod
    def _calculate_dynamic_counts(curriculum: list) -> tuple[int, int, int]:
        """Helper to compute counts of problems, articles, and videos from JSONB curriculum"""
        problems = 0
        articles = 0
        videos = 0
        
        if not curriculum:
            return problems, articles, videos
            
        for section in curriculum:
            # direct items
            items = section.get("items") or []
            for item in items:
                t = item.get("type")
                if t == "problem":
                    problems += 1
                elif t == "article":
                    articles += 1
                elif t == "video":
                    videos += 1
                    
            # subsections items
            subsections = section.get("subsections") or []
            for sub in subsections:
                sub_items = sub.get("items") or []
                for item in sub_items:
                    t = item.get("type")
                    if t == "problem":
                        problems += 1
                    elif t == "article":
                        articles += 1
                    elif t == "video":
                        videos += 1
                        
        return problems, articles, videos

    @staticmethod
    def _format_seconds(seconds: int) -> str:
        """Helper to format video duration_seconds to MM:SS or H:MM:SS"""
        if not seconds or seconds <= 0:
            return "0:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    @staticmethod
    def _hydrate_instructors(instructor_ids: List[str], client: Any) -> List[InstructorSchema]:
        """Fetch co-instructor profiles from instructors table"""
        if not instructor_ids:
            return []
        try:
            response = client.table(CourseService.INSTRUCTORS_TABLE).select("*").in_("id", instructor_ids).execute()
            instructors_map = {item["id"]: item for item in response.data or []}
            
            # Preserve the order defined in instructor_ids
            hydrated = []
            for inst_id in instructor_ids:
                if inst_id in instructors_map:
                    data = instructors_map[inst_id]
                    # Map standard database role/metadata color fields to InstructorSchema
                    metadata = data.get("metadata") or {}
                    color = metadata.get("color") or "from-brand-500 to-blue-500"
                    company = metadata.get("company") or "CrackDSA"
                    
                    hydrated.append(InstructorSchema(
                        name=data["name"],
                        role=data["role"],
                        company=company,
                        color=color
                    ))
            return hydrated
        except Exception as e:
            logger.error(f"Error hydrating instructors: {str(e)}")
            return []

    @staticmethod
    def _hydrate_curriculum_assets(curriculum: list, client: Any) -> list:
        """Dynamically fetch and fill duration_labels and details for all items"""
        if not curriculum:
            return []

        video_ids = []
        problem_slugs = []
        article_slugs = []

        # 1. Harvest all asset IDs/Slugs
        def harvest_items(items):
            for item in items or []:
                t = item.get("type")
                aid = item.get("asset_id")
                if not aid:
                    continue
                if t == "video":
                    video_ids.append(aid)
                elif t == "problem":
                    problem_slugs.append(aid)
                elif t == "article":
                    article_slugs.append(aid)

        for section in curriculum:
            harvest_items(section.get("items"))
            for sub in section.get("subsections") or []:
                harvest_items(sub.get("items"))

        # 2. Bulk fetch asset attributes
        videos_map = {}
        problems_map = {}
        articles_map = {}

        try:
            if video_ids:
                res = client.table(CourseService.VIDEOS_TABLE).select("id, duration_seconds").in_("id", video_ids).execute()
                videos_map = {item["id"]: item for item in res.data or []}
            if problem_slugs:
                res = client.table(CourseService.PROBLEMS_TABLE).select("slug, difficulty").in_("slug", problem_slugs).execute()
                problems_map = {item["slug"]: item for item in res.data or []}
            if article_slugs:
                res = client.table(CourseService.ARTICLES_TABLE).select("slug, read_time_minutes").in_("slug", article_slugs).execute()
                articles_map = {item["slug"]: item for item in res.data or []}
        except Exception as e:
            logger.error(f"Error fetching curriculum asset metadata: {str(e)}")

        # 3. Apply dynamic values back to items in curriculum
        def map_items(items):
            for item in items or []:
                t = item.get("type")
                aid = item.get("asset_id")
                if not aid:
                    continue
                # If duration_label is omitted/empty, calculate it dynamically from database fields
                if not item.get("duration_label"):
                    if t == "video" and aid in videos_map:
                        item["duration_label"] = CourseService._format_seconds(videos_map[aid].get("duration_seconds", 0))
                    elif t == "problem" and aid in problems_map:
                        item["duration_label"] = problems_map[aid].get("difficulty") or "Medium"
                    elif t == "article" and aid in articles_map:
                        read_time = articles_map[aid].get("read_time_minutes") or 5
                        item["duration_label"] = f"{read_time} min read"

        for section in curriculum:
            map_items(section.get("items"))
            for sub in section.get("subsections") or []:
                map_items(sub.get("items"))

        return curriculum

    @staticmethod
    def get_course_summary_by_id(course_id_or_slug: str) -> CourseSummaryResponseSchema:
        """Fetch a specific course summary by UUID or slug, without full curriculum hydration"""
        client = get_supabase_client()
        
        # Check if the query is a valid UUID to decide which column to query
        from uuid import UUID
        is_uuid = False
        try:
            UUID(course_id_or_slug)
            is_uuid = True
        except ValueError:
            is_uuid = False
            
        if is_uuid:
            response = client.table(CourseService.COURSES_TABLE).select("*").eq("id", course_id_or_slug).eq("is_active", True).execute()
        else:
            response = client.table(CourseService.COURSES_TABLE).select("*").eq("slug", course_id_or_slug).eq("is_active", True).execute()
        
        if not response.data or len(response.data) == 0:
            raise ValueError(f"Course with ID or slug '{course_id_or_slug}' not found or inactive")
            
        course_data = response.data[0]
        curriculum = course_data.get("curriculum") or []

        # 1. Calculate dynamic statistics
        problems, articles, videos = CourseService._calculate_dynamic_counts(curriculum)
        course_data["total_problems"] = problems
        course_data["total_articles"] = articles
        course_data["total_videos"] = videos

        # 2. Hydrate instructor profiles list
        instructor_ids = course_data.get("instructor_ids") or []
        course_data["instructors"] = CourseService._hydrate_instructors(instructor_ids, client)

        return CourseSummaryResponseSchema(**course_data)

    @staticmethod
    def get_course_by_id(course_id_or_slug: str) -> CourseResponseSchema:
        """Fetch a specific course full object by UUID or slug (Admin use, ignores is_active)"""
        client = get_supabase_client()
        
        from uuid import UUID
        is_uuid = False
        try:
            UUID(course_id_or_slug)
            is_uuid = True
        except ValueError:
            is_uuid = False
            
        if is_uuid:
            response = client.table(CourseService.COURSES_TABLE).select("*").eq("id", course_id_or_slug).execute()
        else:
            response = client.table(CourseService.COURSES_TABLE).select("*").eq("slug", course_id_or_slug).execute()
        
        if not response.data or len(response.data) == 0:
            raise ValueError(f"Course with ID or slug '{course_id_or_slug}' not found")
            
        course_data = response.data[0]
        curriculum = course_data.get("curriculum") or []

        # Calculate dynamic statistics
        problems, articles, videos = CourseService._calculate_dynamic_counts(curriculum)
        course_data["total_problems"] = problems
        course_data["total_articles"] = articles
        course_data["total_videos"] = videos

        # Hydrate instructor profiles list
        instructor_ids = course_data.get("instructor_ids") or []
        course_data["instructors"] = CourseService._hydrate_instructors(instructor_ids, client)

        return CourseResponseSchema(**course_data)

    @staticmethod
    def get_course_curriculum(course_id_or_slug: str) -> List[CourseSection]:
        """Fetch only the curriculum tree for a specific course by UUID or slug"""
        client = get_supabase_client()
        
        from uuid import UUID
        is_uuid = False
        try:
            UUID(course_id_or_slug)
            is_uuid = True
        except ValueError:
            is_uuid = False
            
        if is_uuid:
            response = client.table(CourseService.COURSES_TABLE).select("curriculum").eq("id", course_id_or_slug).eq("is_active", True).execute()
        else:
            response = client.table(CourseService.COURSES_TABLE).select("curriculum").eq("slug", course_id_or_slug).eq("is_active", True).execute()
        
        if not response.data or len(response.data) == 0:
            raise ValueError(f"Course with ID or slug '{course_id_or_slug}' not found or inactive")
            
        curriculum = response.data[0].get("curriculum") or []
        
        # Hydrate assets
        hydrated_curriculum = CourseService._hydrate_curriculum_assets(curriculum, client)
        
        return [CourseSection(**sec) for sec in hydrated_curriculum]

    @staticmethod
    def list_courses(all_status: bool = False) -> List[CourseSummaryResponseSchema]:
        """Fetch active courses and dynamically populate instructor lists and item counts"""
        client = get_supabase_client()
        
        query = client.table(CourseService.COURSES_TABLE).select("*").eq("is_active", True)
        if not all_status:
            query = query.eq("status", "active")
            
        response = query.execute()
        
        results = []
        for course_data in response.data or []:
            curriculum = course_data.get("curriculum") or []

            # 1. Dynamic totals count
            problems, articles, videos = CourseService._calculate_dynamic_counts(curriculum)
            course_data["total_problems"] = problems
            course_data["total_articles"] = articles
            course_data["total_videos"] = videos

            # 2. Instructors list
            instructor_ids = course_data.get("instructor_ids") or []
            course_data["instructors"] = CourseService._hydrate_instructors(instructor_ids, client)

            # Avoid full asset hydration for general course list to optimize performance
            results.append(CourseSummaryResponseSchema(**course_data))
            
        return results

    # ============ ADMIN CRUD OPERATIONS ============

    @staticmethod
    def create_course(data: CourseCreateSchema) -> CourseResponseSchema:
        """Create a new course in Supabase"""
        client = get_supabase_client()
        
        # Prepare payload
        payload = {
            "slug": data.slug,
            "title": data.title,
            "description": data.description,
            "category": data.category,
            "instructor_ids": [str(inst_id) for inst_id in data.instructor_ids],
            "tags": data.tags,
            "is_pro": data.is_pro,
            "is_popular": data.is_popular,
            "price": data.price,
            "original_price": data.original_price,
            "curriculum": [sec.dict() for sec in data.curriculum] if data.curriculum else [],
            "status": data.status,
            "metadata": data.metadata.model_dump() if data.metadata else {},
        }
        
        if data.id:
            payload["id"] = str(data.id)
        
        response = client.table(CourseService.COURSES_TABLE).insert(payload).execute()
        
        if not response.data or len(response.data) == 0:
            raise Exception("Failed to create course in database")
            
        course_data = response.data[0]
        # Hydrate instructors and compute totals
        problems, articles, videos = CourseService._calculate_dynamic_counts(course_data.get("curriculum") or [])
        course_data["total_problems"] = problems
        course_data["total_articles"] = articles
        course_data["total_videos"] = videos
        course_data["instructors"] = CourseService._hydrate_instructors(course_data.get("instructor_ids") or [], client)
        
        return CourseResponseSchema(**course_data)

    @staticmethod
    def update_course(course_id: str, data: CourseUpdateSchema) -> CourseResponseSchema:
        """Update an existing course"""
        client = get_supabase_client()
        
        # Build update payload
        payload = {}
        if data.slug is not None:
            payload["slug"] = data.slug
        if data.title is not None:
            payload["title"] = data.title
        if data.description is not None:
            payload["description"] = data.description
        if data.category is not None:
            payload["category"] = data.category
        if data.instructor_ids is not None:
            payload["instructor_ids"] = [str(inst_id) for inst_id in data.instructor_ids]
        if data.tags is not None:
            payload["tags"] = data.tags
        if data.is_pro is not None:
            payload["is_pro"] = data.is_pro
        if data.is_popular is not None:
            payload["is_popular"] = data.is_popular
        if data.price is not None:
            payload["price"] = data.price
        if data.original_price is not None:
            payload["original_price"] = data.original_price
        if data.curriculum is not None:
            payload["curriculum"] = [sec.dict() for sec in data.curriculum]
        if data.status is not None:
            payload["status"] = data.status
        if data.metadata is not None:
            payload["metadata"] = data.metadata.model_dump()
            
        payload["updated_at"] = "now()"
        
        response = client.table(CourseService.COURSES_TABLE).update(payload).eq("id", course_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise ValueError(f"Course '{course_id}' not found or update failed")
            
        course_data = response.data[0]
        # Hydrate instructors and compute totals
        problems, articles, videos = CourseService._calculate_dynamic_counts(course_data.get("curriculum") or [])
        course_data["total_problems"] = problems
        course_data["total_articles"] = articles
        course_data["total_videos"] = videos
        course_data["instructors"] = CourseService._hydrate_instructors(course_data.get("instructor_ids") or [], client)
        
        return CourseResponseSchema(**course_data)

    @staticmethod
    def delete_course(course_id: str, hard_delete: bool = False) -> bool:
        """Delete a course (soft delete by default)"""
        client = get_supabase_client()
        
        if hard_delete:
            client.table(CourseService.COURSES_TABLE).delete().eq("id", course_id).execute()
        else:
            client.table(CourseService.COURSES_TABLE).update({"is_active": False, "updated_at": "now()"}).eq("id", course_id).execute()
            
        logger.info(f"Deleted course: {course_id} (hard={hard_delete})")
        return True
