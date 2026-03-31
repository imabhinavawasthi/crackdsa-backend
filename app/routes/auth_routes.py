"""
Authentication routes - wrapper around Supabase.

Frontend handles complete Supabase OAuth flow.
Backend provides utility endpoints.
"""

from fastapi import APIRouter, HTTPException, Response, Depends
from typing import Dict, Any, Optional
from app.dependencies import get_current_user, get_current_user_optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.get("/me")
async def me(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user data from Supabase."""
    return user


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing Supabase token cookies."""
    try:
        response.delete_cookie(key="supabase_token", path="/")
        response.delete_cookie(key="supabase_refresh_token", path="/")
        
        logger.info("Tokens cleared on logout")
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/token-status")
async def token_status(user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Check if user has a valid token."""
    return {"authenticated": user is not None}
