from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from app.schemas.contest_editorial import ContestSummary, ContestDetail, ContestSuggestionCreate, ContestPaginatedResponse
from app.controllers import contest_controller
from app.dependencies import get_token

router = APIRouter(
    prefix="/contests",
    tags=["Contest Editorials"]
)

@router.get("/paginated", response_model=ContestPaginatedResponse)
async def list_contests_paginated(
    platform: Optional[str] = Query(None, description="Filter by platform (e.g. codeforces, leetcode, codechef)"),
    search: Optional[str] = Query(None, description="Search term for contest title or platform"),
    sort_by: Optional[str] = Query("latest", description="Sort order: latest, oldest, problems"),
    limit: Optional[int] = Query(10, ge=1, le=100, description="Limit number of contests returned per page"),
    page: Optional[int] = Query(1, ge=1, description="Page number (1-indexed)"),
    token: Optional[str] = Depends(get_token)
):
    """
    List programming contests with pagination metadata (items, total_count, total_pages, platforms, stats).
    """
    return await contest_controller.list_contests_paginated_handler(
        platform=platform,
        search=search,
        sort_by=sort_by,
        limit=limit or 10,
        page=page or 1,
        token=token
    )

@router.get("", response_model=List[ContestSummary])
async def list_contests(
    platform: Optional[str] = Query(None, description="Filter by platform (e.g. codeforces, leetcode, codechef)"),
    search: Optional[str] = Query(None, description="Search term for contest title or platform"),
    sort_by: Optional[str] = Query("latest", description="Sort order: latest, oldest, problems"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of contests returned"),
    page: Optional[int] = Query(1, ge=1, description="Page number (1-indexed)"),
    token: Optional[str] = Depends(get_token)
):
    """
    List programming contests with aggregated problem metrics and difficulty distribution.
    Supports limit and page for dashboard and pagination.
    """
    return await contest_controller.list_contests_handler(
        platform=platform, 
        search=search, 
        sort_by=sort_by,
        limit=limit, 
        page=page, 
        token=token
    )

@router.get("/{platform}/{contest_slug}", response_model=ContestDetail)
async def get_contest_detail(
    platform: str,
    contest_slug: str,
    token: Optional[str] = Depends(get_token)
):
    """
    Get detailed contest overview and all problem editorials for a specific contest.
    """
    return await contest_controller.get_contest_detail_handler(platform=platform, contest_slug=contest_slug, token=token)

@router.get("/{platform}/{contest_slug}/problems/{problem_slug}")
async def get_contest_problem_editorial(
    platform: str,
    contest_slug: str,
    problem_slug: str,
    token: Optional[str] = Depends(get_token)
):
    """
    Get a single contest problem with its video editorial, written explanation, and sibling navigation.
    """
    return await contest_controller.get_problem_editorial_handler(
        platform=platform, 
        contest_slug=contest_slug, 
        problem_slug=problem_slug, 
        token=token
    )

@router.post("/suggest")
async def suggest_contest(
    suggestion: ContestSuggestionCreate,
    token: Optional[str] = Depends(get_token)
):
    """
    Submit a contest request or suggestion.
    """
    return await contest_controller.suggest_contest_handler(suggestion=suggestion, token=token)
