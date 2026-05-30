from app.database import get_supabase_client
from app.schemas.instructor import (
    InstructorCreateSchema,
    InstructorUpdateSchema,
    InstructorResponseSchema,
)
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class InstructorService:
    """Service layer for instructor CRUD operations"""

    TABLE_NAME = "instructors"

    @staticmethod
    def create_instructor(data: InstructorCreateSchema) -> InstructorResponseSchema:
        """
        Create a new instructor.
        
        Args:
            data: InstructorCreateSchema with instructor details
            
        Returns:
            InstructorResponseSchema with created instructor data
            
        Raises:
            Exception: If database operation fails
        """
        try:
            client = get_supabase_client()
            
            # Prepare payload
            payload = {
                "name": data.name,
                "role": data.role,
                "sub_title": data.sub_title,
                "bio": data.bio,
                "profile_image_url": data.profile_image_url,
                "metadata": data.metadata or {},
            }
            
            # Insert into database
            response = client.table(InstructorService.TABLE_NAME).insert(payload).execute()
            
            if not response.data or len(response.data) == 0:
                raise Exception("Failed to create instructor: No data returned from database")
            
            instructor = response.data[0]
            logger.info(f"Created instructor: {instructor['id']}")
            
            return InstructorResponseSchema(**instructor)
            
        except Exception as e:
            logger.error(f"Error creating instructor: {str(e)}")
            raise

    @staticmethod
    def get_instructor_by_id(instructor_id: UUID) -> InstructorResponseSchema:
        """
        Fetch a single instructor by ID.
        
        Args:
            instructor_id: UUID of the instructor
            
        Returns:
            InstructorResponseSchema
            
        Raises:
            Exception: If instructor not found or database error
        """
        try:
            client = get_supabase_client()
            
            response = client.table(InstructorService.TABLE_NAME).select(
                "*"
            ).eq(
                "id", str(instructor_id)
            ).eq(
                "is_active", True
            ).execute()
            
            if not response.data or len(response.data) == 0:
                raise Exception(f"Instructor with id {instructor_id} not found")
            
            instructor = response.data[0]
            return InstructorResponseSchema(**instructor)
            
        except Exception as e:
            logger.error(f"Error fetching instructor {instructor_id}: {str(e)}")
            raise

    @staticmethod
    def list_instructors(limit: int = 20, offset: int = 0, include_inactive: bool = False):
        """
        List all instructors with pagination.
        
        Args:
            limit: Number of instructors to fetch
            offset: Number of instructors to skip
            include_inactive: Whether to include inactive instructors (admin only)
            
        Returns:
            Dictionary with items, total, limit, offset
        """
        try:
            client = get_supabase_client()
            
            # Build query
            query = client.table(InstructorService.TABLE_NAME).select("*", count="exact")
            
            # Filter by active status if not including inactive
            if not include_inactive:
                query = query.eq("is_active", True)
            
            # Apply pagination
            response = query.range(offset, offset + limit - 1).execute()
            
            instructors = [InstructorResponseSchema(**item) for item in response.data]
            total = response.count or 0
            
            logger.info(f"Listed {len(instructors)} instructors (total: {total})")
            
            return {
                "items": instructors,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
            
        except Exception as e:
            logger.error(f"Error listing instructors: {str(e)}")
            raise

    @staticmethod
    def update_instructor(instructor_id: UUID, data: InstructorUpdateSchema) -> InstructorResponseSchema:
        """
        Update an instructor's details.
        
        Args:
            instructor_id: UUID of the instructor
            data: InstructorUpdateSchema with fields to update
            
        Returns:
            InstructorResponseSchema with updated data
            
        Raises:
            Exception: If instructor not found or update fails
        """
        try:
            client = get_supabase_client()
            
            # Build update payload (only non-None fields)
            update_payload = {}
            if data.name is not None:
                update_payload["name"] = data.name
            if data.role is not None:
                update_payload["role"] = data.role
            if data.sub_title is not None:
                update_payload["sub_title"] = data.sub_title
            if data.bio is not None:
                update_payload["bio"] = data.bio
            if data.profile_image_url is not None:
                update_payload["profile_image_url"] = data.profile_image_url
            if data.metadata is not None:
                update_payload["metadata"] = data.metadata
            if data.is_active is not None:
                update_payload["is_active"] = data.is_active
            
            # Always update the updated_at timestamp
            update_payload["updated_at"] = "now()"
            
            # Update in database
            response = client.table(InstructorService.TABLE_NAME).update(
                update_payload
            ).eq(
                "id", str(instructor_id)
            ).execute()
            
            if not response.data or len(response.data) == 0:
                raise Exception(f"Instructor with id {instructor_id} not found or update failed")
            
            instructor = response.data[0]
            logger.info(f"Updated instructor: {instructor_id}")
            
            return InstructorResponseSchema(**instructor)
            
        except Exception as e:
            logger.error(f"Error updating instructor {instructor_id}: {str(e)}")
            raise

    @staticmethod
    def delete_instructor(instructor_id: UUID, hard_delete: bool = False) -> bool:
        """
        Delete an instructor (soft delete by default, can be hard delete).
        
        Args:
            instructor_id: UUID of the instructor
            hard_delete: If True, permanently delete; if False, soft delete (set is_active=false)
            
        Returns:
            True if deletion successful
            
        Raises:
            Exception: If deletion fails
        """
        try:
            client = get_supabase_client()
            
            if hard_delete:
                # Permanent deletion
                response = client.table(InstructorService.TABLE_NAME).delete().eq(
                    "id", str(instructor_id)
                ).execute()
            else:
                # Soft delete
                response = client.table(InstructorService.TABLE_NAME).update(
                    {"is_active": False, "updated_at": "now()"}
                ).eq(
                    "id", str(instructor_id)
                ).execute()
            
            logger.info(f"Deleted instructor: {instructor_id} (hard_delete={hard_delete})")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting instructor {instructor_id}: {str(e)}")
            raise

    @staticmethod
    def search_instructors(query: str, limit: int = 20) -> list[InstructorResponseSchema]:
        """
        Search instructors by name or role.
        
        Args:
            query: Search query string
            limit: Maximum results to return
            
        Returns:
            List of matching instructors
        """
        try:
            client = get_supabase_client()
            
            # Use Postgres full-text search or simple ILIKE
            response = client.table(InstructorService.TABLE_NAME).select(
                "*"
            ).or_(
                f"name.ilike.%{query}%,role.ilike.%{query}%"
            ).eq(
                "is_active", True
            ).limit(limit).execute()
            
            instructors = [InstructorResponseSchema(**item) for item in response.data]
            logger.info(f"Searched instructors for '{query}': found {len(instructors)}")
            
            return instructors
            
        except Exception as e:
            logger.error(f"Error searching instructors: {str(e)}")
            raise
