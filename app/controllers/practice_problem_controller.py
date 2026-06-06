from typing import List
from fastapi import HTTPException
from app.schemas.practice_problem import PracticeProblemCreate, PracticeProblemUpdate
from app.services import practice_problem_service
from uuid import UUID

async def list_problems_handler(include_inactive: bool = False, token: str = None) -> List[dict]:
    """
    Controller handler to list practice problems.
    """
    try:
        return practice_problem_service.get_practice_problems(include_inactive=include_inactive, token=token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch practice problems: {str(e)}")

async def list_problems_basic_handler(include_inactive: bool = False, token: str = None) -> List[dict]:
    """
    Controller handler to list only basic details of practice problems.
    """
    try:
        return practice_problem_service.get_practice_problems_basic(include_inactive=include_inactive, token=token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch basic practice problems: {str(e)}")

async def get_problem_handler(problem_id: UUID, include_inactive: bool = False, token: str = None) -> dict:
    """
    Controller handler to retrieve a single problem by UUID.
    """
    try:
        problem = practice_problem_service.get_practice_problem_by_id(problem_id, include_inactive=include_inactive, token=token)
        if not problem:
            raise HTTPException(status_code=404, detail="Practice problem not found")
        return problem
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_problem_by_slug_handler(slug: str, include_inactive: bool = False, token: str = None) -> dict:
    """
    Controller handler to retrieve a single problem by slug.
    """
    try:
        problem = practice_problem_service.get_practice_problem_by_slug(slug, include_inactive=include_inactive, token=token)
        if not problem:
            raise HTTPException(status_code=404, detail="Practice problem not found")
        return problem
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_problem_handler(problem_data: PracticeProblemCreate, token: str = None) -> dict:
    """
    Controller handler to create a new practice problem.
    """
    try:
        return practice_problem_service.create_practice_problem(problem_data, token=token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def update_problem_handler(problem_id: UUID, update_data: PracticeProblemUpdate, token: str = None) -> dict:
    """
    Controller handler to update an existing practice problem.
    """
    try:
        return practice_problem_service.update_practice_problem(problem_id, update_data, token=token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def delete_problem_handler(problem_id: UUID, token: str = None) -> dict:
    """
    Controller handler to soft-delete an existing practice problem.
    """
    try:
        practice_problem_service.soft_delete_practice_problem(problem_id, token=token)
        return {"message": "Practice problem deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
