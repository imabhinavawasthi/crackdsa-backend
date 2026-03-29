"""
Authentication routes - wrapper around Supabase.

Frontend handles complete Supabase OAuth flow.
Backend just stores tokens and provides utility endpoints.

Endpoints:
- GET /api/v1/auth/me - Get current user data from Supabase
- POST /api/v1/auth/logout - Clear tokens
- GET /api/v1/auth/token-status - Check if authenticated
"""

from fastapi import APIRouter, HTTPException, Response, Cookie, Header
from typing import Optional
from app.database import get_supabase_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.get("/me")
async def get_current_user(
    supabase_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    """
    Get current authenticated user data from Supabase.
    
    Uses token from either:
    1. HTTP-only cookie (supabase_token)
    2. Authorization header (Bearer token)
    
    Returns:
        dict: User data from Supabase with the following fields:
            - id: User UUID
            - email: User email address
            - full_name: User's full name
            - avatar_url: User's avatar URL
            - email_verified: Whether email is verified
            - phone: User's phone number
            - provider: OAuth provider (e.g., 'google')
            - created_at: Account creation timestamp
            - last_sign_in_at: Last login timestamp
        
    Raises:
        401: If no valid token or user not found
        
    Example:
        GET /api/v1/auth/me
        Authorization: Bearer <token>
        
        Response (HTTP 200):
        {
            "id": "96718f5f-3083-467f-8e45-980b5a6db8d1",
            "email": "user@example.com",
            "full_name": "John Doe",
            "avatar_url": "https://lh3.googleusercontent.com/...",
            "email_verified": true,
            "phone": "+1234567890",
            "provider": "google",
            "created_at": "2024-03-24T08:28:53.784675",
            "last_sign_in_at": "2026-03-29T19:56:18.135833"
        }
    """
    try:
        # Get token from cookie or Authorization header
        token = supabase_token
        
        if not token and authorization:
            # Extract token from "Bearer <token>"
            if authorization.startswith("Bearer "):
                token = authorization[7:]
            else:
                token = authorization
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail="No authentication token provided"
            )
        
        # Get Supabase client and verify token
        client = get_supabase_client()
        
        try:
            # Verify token and get user
            response = client.auth.get_user(token)
            
            # Extract user from UserResponse object
            user = response.user if hasattr(response, 'user') else response
            
            logger.info(f"User fetched: {user.email}")
            
            # Extract user metadata and app metadata from the User object
            user_metadata = user.user_metadata or {}
            app_metadata = user.app_metadata or {}
            
            # Build clean response with all relevant fields
            # Convert datetime objects to ISO format strings for JSON serialization
            return {
                "id": user.id,
                "email": user.email,
                "full_name": user_metadata.get('full_name') or user_metadata.get('name'),
                "avatar_url": user_metadata.get('avatar_url') or user_metadata.get('picture'),
                "email_verified": user_metadata.get('email_verified', False),
                "phone": user.phone or '',
                "provider": app_metadata.get('provider'),
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_sign_in_at": user.last_sign_in_at.isoformat() if user.last_sign_in_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            }
            
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching user: {str(e)}"
        )


@router.post("/logout")
async def logout(response: Response):
    """
    Logout user by clearing Supabase token cookies.
    
    Frontend should:
    1. Call supabase.auth.signOut()
    2. Call this endpoint to clear server-side cookies
    
    Returns:
        dict: Success message
    """
    try:
        # Clear the Supabase token cookies
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
async def check_token(supabase_token: Optional[str] = Cookie(None)):
    """
    Check if user has a valid token.
    
    Returns:
        dict: Token status
    """
    return {
        "authenticated": supabase_token is not None,
        "has_token": supabase_token is not None
    }
