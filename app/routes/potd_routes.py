from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/potd",
    tags=["Problem of the Day"],
)


@router.get("")
async def get_problem_of_the_day():
    """
    Returns today's Problem of the Day.

    Public endpoint — no authentication required.
    The problem is selected deterministically based on the current date
    so all users see the same problem on any given day.
    """
    from app.services.potd_service import get_problem_of_the_day as potd_service

    problem = potd_service()

    if not problem:
        raise HTTPException(
            status_code=404,
            detail="No problem of the day available at this time.",
        )

    return problem
