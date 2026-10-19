from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from app.services import contest_service
from app.schemas.contest_editorial import ContestSuggestionCreate

async def list_contests_handler(
    platform: Optional[str] = None, 
    search: Optional[str] = None, 
    token: Optional[str] = None
) -> List[Dict[str, Any]]:
    try:
        return contest_service.get_contests(platform=platform, search=search, token=token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch contests: {str(e)}")

async def get_contest_detail_handler(
    platform: str, 
    contest_slug: str, 
    token: Optional[str] = None
) -> Dict[str, Any]:
    try:
        contest = contest_service.get_contest_detail(platform=platform, contest_slug=contest_slug, token=token)
        if not contest:
            raise HTTPException(status_code=404, detail="Contest not found")
        return contest
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_problem_editorial_handler(
    platform: str,
    contest_slug: str,
    problem_slug: str,
    token: Optional[str] = None
) -> Dict[str, Any]:
    try:
        result = contest_service.get_problem_editorial(platform, contest_slug, problem_slug, token=token)
        if not result:
            raise HTTPException(status_code=404, detail="Contest problem editorial not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def suggest_contest_handler(
    suggestion: ContestSuggestionCreate, 
    token: Optional[str] = None
) -> Dict[str, Any]:
    # Acknowledge suggestion
    return {
        "status": "success",
        "message": f"Thank you! Your suggestion for {suggestion.contest_name} ({suggestion.platform}) has been recorded."
    }
