"""
Test routes for demonstrating RBAC (Role-Based Access Control) functionality.

Usage examples:
- Require specific role: require_role("admin")
- Require any of multiple roles: require_any_role(["admin", "moderator"])
- Use convenience dependencies: require_admin, require_support_team, require_moderator
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List, Optional
from app.dependencies import (
    get_current_token,
    get_current_user,
    get_current_user_optional,
    get_current_user_with_token,
    require_role_with_token,
    require_any_role_with_token
)

router = APIRouter(prefix="/api/v1/test-rbac", tags=["RBAC Tests"])


# Public endpoint - no auth required
@router.get("/public")
async def public_endpoint():
    """Public endpoint, accessible by anyone."""
    return {"message": "This is a public endpoint"}


# Authenticated endpoint - any authenticated user
@router.get("/authenticated")
async def authenticated_endpoint(data: Dict[str, Any] = Depends(get_current_user_with_token)):
    """Authenticated endpoint, requires valid token. Returns both user and token."""
    user = data["user"]
    return {
        "message": f"Hello {user['full_name'] or user['email']}",
        "user_id": user['id'],
        "email": user['email'],
        "token_present": data["token"] is not None
    }


# Get current user with roles
@router.get("/me-with-roles")
async def get_user_with_roles(
    data: Dict[str, Any] = Depends(get_current_user_with_token)
):
    """Get current user with their assigned roles and the JWT."""
    user = data["user"]
    from app.dependencies import _get_user_roles # Local import for testing
    roles = _get_user_roles(user['email'])
    return {
        "user_id": user['id'],
        "email": user['email'],
        "full_name": user['full_name'],
        "roles": roles,
        "token_present": data["token"] is not None
    }


# Admin-only endpoint
@router.get("/admin-only")
async def admin_only(auth_data: Dict[str, Any] = Depends(require_role_with_token("admin"))):
    """Admin-only endpoint. Requires 'admin' role. Passes token for RLS."""
    user = auth_data["user"]
    return {
        "message": "Admin access granted",
        "user_email": user['email'],
        "roles": user['roles'],
        "token_present": auth_data["token"] is not None
    }


# Support team-only endpoint
@router.get("/support-only")
async def support_only(auth_data: Dict[str, Any] = Depends(require_role_with_token("support_team"))):
    """Support team-only endpoint. Requires 'support_team' role."""
    user = auth_data["user"]
    return {
        "message": "Support team access granted",
        "user_email": user['email'],
        "roles": user['roles']
    }


# Moderator-only endpoint
@router.get("/moderator-only")
async def moderator_only(auth_data: Dict[str, Any] = Depends(require_role_with_token("moderator"))):
    """Moderator-only endpoint. Requires 'moderator' role."""
    user = auth_data["user"]
    return {
        "message": "Moderator access granted",
        "user_email": user['email'],
        "roles": user['roles']
    }


# Admin or Moderator endpoint (using require_any_role_with_token)
@router.get("/admin-or-moderator")
async def admin_or_moderator(
    auth_data: Dict[str, Any] = Depends(require_any_role_with_token(["admin", "moderator"]))
):
    """Endpoint that requires either admin or moderator role."""
    user = auth_data["user"]
    return {
        "message": "Admin or Moderator access granted",
        "user_email": user['email'],
        "roles": user['roles']
    }


# Admin or Support Team endpoint
@router.get("/admin-or-support")
async def admin_or_support(
    auth_data: Dict[str, Any] = Depends(require_any_role_with_token(["admin", "support_team"]))
):
    """Endpoint that requires either admin or support_team role."""
    user = auth_data["user"]
    return {
        "message": "Admin or Support Team access granted",
        "user_email": user['email'],
        "roles": user['roles']
    }


# Optional auth with role info (if authenticated)
@router.get("/optional-with-roles")
async def optional_auth_with_roles(user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Optional auth endpoint that shows roles if user is authenticated."""
    if user:
        from app.dependencies import _get_user_roles # Local import for testing
        roles = _get_user_roles(user['email'])
        return {
            "authenticated": True,
            "user_email": user['email'],
            "roles": roles,
            "has_admin": "admin" in roles,
        }
    else:
        return {
            "authenticated": False,
            "message": "No authentication token provided",
        }
