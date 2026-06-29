from typing import List, Optional
from fastapi import APIRouter, Depends
from app.schemas.practice_problem import PracticeProblem, PracticeProblemCreate, PracticeProblemUpdate, PracticeProblemBasic
from app.controllers import practice_problem_controller
from app.dependencies import require_role_with_token, get_token
from uuid import UUID

# --- Public Router ---
# General student access: only list active problems and retrieve by ID or Slug
public_router = APIRouter(
    prefix="/practice-problems",
    tags=["Practice Problems (Public)"]
)

@public_router.get("", response_model=List[PracticeProblemBasic])
async def list_problems_public(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    token: Optional[str] = Depends(get_token)
):
    """
    List all active practice problems for student discovery. Supports limit and offset pagination.
    """
    return await practice_problem_controller.list_problems_basic_handler(
        include_inactive=False, 
        token=token,
        limit=limit,
        offset=offset
    )

@public_router.get("/topics-summary")
async def get_topics_summary_route(token: Optional[str] = Depends(get_token)):
    """
    Get a summary of all topics with problem counts.
    """
    from app.services.practice_problem_service import get_topics_summary
    return get_topics_summary(token=token)

@public_router.get("/companies-summary")
async def get_companies_summary_route(token: Optional[str] = Depends(get_token)):
    """
    Get a summary of all companies with problem counts.
    """
    from app.services.practice_problem_service import get_companies_summary
    return get_companies_summary(token=token)

@public_router.get("/topics/{topic_slug}", response_model=List[PracticeProblemBasic])
async def list_problems_by_topic(topic_slug: str, token: Optional[str] = Depends(get_token)):
    """
    List active practice problems matching a specific topic tag (slugified).
    """
    from app.services.practice_problem_service import get_practice_problems_by_topic
    return get_practice_problems_by_topic(topic_slug, token=token)

@public_router.get("/companies/{company_slug}", response_model=List[PracticeProblemBasic])
async def list_problems_by_company(company_slug: str, token: Optional[str] = Depends(get_token)):
    """
    List active practice problems matching a specific company tag (slugified).
    """
    from app.services.practice_problem_service import get_practice_problems_by_company
    return get_practice_problems_by_company(company_slug, token=token)

@public_router.get("/{slug_or_id}", response_model=PracticeProblem)
async def get_problem_public(slug_or_id: str, token: Optional[str] = Depends(get_token)):
    """
    Get a single active practice problem by its UUID or unique slug.
    """
    try:
        problem_id = UUID(slug_or_id)
        return await practice_problem_controller.get_problem_handler(problem_id, include_inactive=False, token=token)
    except ValueError:
        return await practice_problem_controller.get_problem_by_slug_handler(slug_or_id, include_inactive=False, token=token)


# --- Admin Router ---
# Full CRUD control: reserved for SDE moderators, includes soft-deleted items
admin_router = APIRouter(
    prefix="/admin/practice-problems",
    tags=["Practice Problems (Admin)"]
)

@admin_router.get("", response_model=List[PracticeProblemBasic])
async def list_problems_admin(auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    List all practice problems (active + soft-deleted) for administrative audit.
    Requires 'admin' role.
    """
    return await practice_problem_controller.list_problems_basic_handler(include_inactive=True, token=auth_data["token"])

@admin_router.get("/{id}", response_model=PracticeProblem)
async def get_problem_admin(id: UUID, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Get any practice problem by its UUID (even if soft-deleted).
    Requires 'admin' role.
    """
    return await practice_problem_controller.get_problem_handler(id, include_inactive=True, token=auth_data["token"])

@admin_router.post("", response_model=PracticeProblem)
async def create_problem_admin(problem_data: PracticeProblemCreate, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Create a new reusable practice problem asset.
    Requires 'admin' role.
    """
    return await practice_problem_controller.create_problem_handler(problem_data, token=auth_data["token"])

@admin_router.put("/{id}", response_model=PracticeProblem)
async def update_problem_admin(id: UUID, update_data: PracticeProblemUpdate, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Update an existing practice problem asset details (supports partial updates).
    Requires 'admin' role.
    """
    return await practice_problem_controller.update_problem_handler(id, update_data, token=auth_data["token"])

@admin_router.delete("/{id}")
async def delete_problem_admin(id: UUID, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Soft delete a practice problem.
    Requires 'admin' role.
    """
    return await practice_problem_controller.delete_problem_handler(id, token=auth_data["token"])
