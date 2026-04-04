"""
Test routes to demonstrate authentication and authorization.

These are example routes showing how to use the authentication dependencies.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.dependencies import get_current_user, get_current_user_optional, get_current_user_with_token, get_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/test",
    tags=["Testing"]
)


@router.get("/public")
async def test_public():
    """
    Public endpoint - No authentication required.
    """
    return {
        "message": "This is a public endpoint",
        "requires_auth": False,
        "status": "success"
    }


@router.get("/authenticated")
async def test_authenticated(data: Dict[str, Any] = Depends(get_current_user_with_token)):
    """
    Protected endpoint - Requires valid Bearer token.
    Now captures the token for RLS demonstration.
    """
    user = data["user"]
    logger.info(f"Authenticated test endpoint accessed by user: {user['email']}")
    
    return {
        "message": f"Hello {user['full_name']}! You are authenticated",
        "requires_auth": True,
        "user": user,
        "token_present": data["token"] is not None
    }


@router.get("/optional-auth")
async def test_optional_auth(user: Dict[str, Any] = Depends(get_current_user_optional)):
    """
    Endpoint with optional authentication.
    
    Works both with and without a token. If user is authenticated, returns user data.
    If not authenticated, returns public content.
    
    Args:
        user: Current authenticated user if token provided, None otherwise
    
    Returns:
        dict: Response with or without user data
        
    Example (with token):
        curl -H "Authorization: Bearer <your_token>" http://localhost:8000/api/v1/test/optional-auth
        
    Response (HTTP 200 - Authenticated):
        {
            "message": "Welcome back, John Doe!",
            "is_authenticated": true,
            "user": { ... user data ... }
        }
        
    Example (without token):
        curl http://localhost:8000/api/v1/test/optional-auth
        
    Response (HTTP 200 - Not Authenticated):
        {
            "message": "Welcome guest! Sign in to see personalized content",
            "is_authenticated": false,
            "user": null
        }
    """
    if user:
        logger.info(f"Optional auth endpoint - Authenticated user: {user['email']}")
        return {
            "message": f"Welcome back, {user['full_name']}!",
            "is_authenticated": True,
            "user": user
        }
    else:
        logger.info("Optional auth endpoint - Guest access")
        return {
            "message": "Welcome guest! Sign in to see personalized content",
            "is_authenticated": False,
            "user": None
        }
