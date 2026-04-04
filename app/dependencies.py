"""
Authentication dependencies for FastAPI routes.

Centralized auth logic with extracted helper functions to eliminate duplication.
Includes RBAC (Role-Based Access Control) dependencies for role checking.
"""

from fastapi import HTTPException, Header, Cookie, Depends
from typing import Optional, Dict, Any, List, Callable
from app.database import get_supabase_client
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def _extract_token_from_header(
    supabase_token: Optional[str],
    authorization: Optional[str]
) -> Optional[str]:
    """Extract token from cookie or Authorization header."""
    token = supabase_token
    
    if not token and authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization
    
    return token


def _build_user_response(user: Any) -> Dict[str, Any]:
    """Build clean user data dict from Supabase User object."""
    user_metadata = user.user_metadata or {}
    app_metadata = user.app_metadata or {}
    
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


def _get_user_roles(email: str) -> List[str]:
    """Get all roles assigned to a user based on their email."""
    roles = []
    role_mapping = settings.role_mapping
    
    for role_name, emails in role_mapping.items():
        if email in emails:
            roles.append(role_name)
    
    return roles


async def get_current_user(
    supabase_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """Dependency to extract and validate the current authenticated user."""
    try:
        token = _extract_token_from_header(supabase_token, authorization)
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail="No authentication token provided"
            )
        
        client = get_supabase_client()
        
        try:
            response = client.auth.get_user(token)
            user = response.user if hasattr(response, 'user') else response
            
            logger.info(f"User authenticated: {user.email}")
            return _build_user_response(user)
            
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Authentication verification failed"
        )


async def get_current_user_optional(
    supabase_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """Optional auth dependency. Returns user data if authenticated, None otherwise."""
    try:
        token = _extract_token_from_header(supabase_token, authorization)
        
        if not token:
            return None
        
        client = get_supabase_client()
        
        try:
            response = client.auth.get_user(token)
            user = response.user if hasattr(response, 'user') else response
            
            logger.info(f"Optional auth - User present: {user.email}")
            return _build_user_response(user)
            
        except Exception as e:
            logger.info(f"Optional auth - Invalid token: {str(e)}")
            return None
        
    except Exception as e:
        logger.info(f"Optional authentication check: {str(e)}")
        return None


async def get_current_user_with_roles(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user with their assigned roles."""
    roles = _get_user_roles(user['email'])
    user['roles'] = roles
    return user


async def get_token(
    supabase_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """Dependency to extract the raw Authentication token."""
    return _extract_token_from_header(supabase_token, authorization)

# Alias for backward compatibility or different naming preference
get_current_token = get_token


async def get_current_user_with_token(
    user: Dict[str, Any] = Depends(get_current_user),
    token: str = Depends(get_token)
) -> Dict[str, Any]:
    """Get the current authenticated user and return both user data and the token."""
    if not token:
        raise HTTPException(status_code=401, detail="No authentication token provided")
    
    return {"user": user, "token": token}


def require_role(required_role: str) -> Callable:
    """
    Create a dependency that requires a specific role.
    
    Usage:
        @router.get("/admin-endpoint")
        async def admin_endpoint(user = Depends(require_role("admin"))):
            return {"message": "Admin only"}
    """
    async def dependency(
        user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Check if user has the required role."""
        roles = _get_user_roles(user['email'])
        
        if required_role not in roles:
            logger.warning(
                f"Access denied: User {user['email']} tried to access {required_role} "
                f"resource but only has roles: {roles}"
            )
            raise HTTPException(
                status_code=403,
                detail="Not allowed to perform this action"
            )
        
        user['roles'] = roles
        return user
    
    return dependency


def require_role_with_token(required_role: str) -> Callable:
    """Dependency that requires a role AND returns the token for RLS use."""
    async def dependency(
        data: Dict[str, Any] = Depends(get_current_user_with_token)
    ) -> Dict[str, Any]:
        user = data["user"]
        token = data["token"]
        
        roles = _get_user_roles(user['email'])
        if required_role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires {required_role} role")
        
        user['roles'] = roles
        return {"user": user, "token": token}
    
    return dependency


def require_any_role_with_token(required_roles: List[str]) -> Callable:
    """Dependency that requires any of the roles AND returns the token for RLS use."""
    async def dependency(
        data: Dict[str, Any] = Depends(get_current_user_with_token)
    ) -> Dict[str, Any]:
        user = data["user"]
        token = data["token"]
        
        user_roles = _get_user_roles(user['email'])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(status_code=403, detail=f"Requires one of {required_roles} roles")
        
        user['roles'] = user_roles
        return {"user": user, "token": token}
    
    return dependency


def require_any_role(required_roles: List[str]) -> Callable:
    """
    Create a dependency that requires at least one of the specified roles.
    
    Usage:
        @router.get("/restricted")
        async def restricted(
            user = Depends(require_any_role(["admin", "moderator"]))
        ):
            return {"message": "Admin or Moderator only"}
    """
    async def dependency(
        user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Check if user has at least one of the required roles."""
        user_roles = _get_user_roles(user['email'])
        
        if not any(role in user_roles for role in required_roles):
            logger.warning(
                f"Access denied: User {user['email']} tried to access resource requiring "
                f"one of {required_roles} but only has roles: {user_roles}"
            )
            raise HTTPException(
                status_code=403,
                detail="Not allowed to perform this action"
            )
        
        user['roles'] = user_roles
        return user
    
    return dependency


# Use require_role("role_name") directly in routes for any role
# Examples:
#   admin: Depends(require_role("admin"))
#   support_team: Depends(require_role("support_team"))
#   moderator: Depends(require_role("moderator"))
#   custom_role: Depends(require_role("custom_role"))

