import asyncio
from app.services.course_service import CourseService
from app.schemas.course import CourseResponseSchema
import traceback

async def main():
    try:
        courses = CourseService.list_courses(all_status=True)
        print("Courses retrieved successfully:", len(courses))
        for c in courses:
            try:
                # Try to validate via pydantic
                CourseResponseSchema.model_validate(c)
            except Exception as e:
                print(f"Validation failed for course {c.get('id') if isinstance(c, dict) else c.id}:")
                traceback.print_exc()
    except Exception as e:
        print("Exception inside list_courses:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
