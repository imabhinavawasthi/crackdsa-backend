"""
Test routes for demonstrating RBAC (Role-Based Access Control) functionality.

Usage examples:
- Require specific role: require_role("admin")
- Require any of multiple roles: require_any_role(["admin", "moderator"])
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_current_user_with_roles,
    require_role,
    require_any_role,
)

router = APIRouter(prefix="/api/v1/test-rbac", tags=["Testing - RBAC"])


# Public endpoint - no auth required
@router.get("/public")
async def public_endpoint():
    """Public endpoint, accessible by anyone."""
    return {"message": "This is a public endpoint"}


# Authenticated endpoint - any authenticated user
@router.get("/authenticated")
async def authenticated_endpoint(user: Dict[str, Any] = Depends(get_current_user)):
    """Authenticated endpoint, requires valid token."""
    return {
        "message": f"Hello {user['full_name'] or user['email']}",
        "user_id": user['id'],
        "email": user['email'],
    }


# Get current user with roles
@router.get("/me-with-roles")
async def get_user_with_roles(
    user: Dict[str, Any] = Depends(get_current_user_with_roles)
):
    """Get current user with their assigned roles."""
    return {
        "user_id": user['id'],
        "email": user['email'],
        "full_name": user['full_name'],
        "roles": user.get('roles', []),
    }


# Admin-only endpoint
@router.get("/admin-only")
async def admin_only(user: Dict[str, Any] = Depends(require_role("admin"))):
    """Admin-only endpoint. Returns 403 if user doesn't have admin role."""
    return {
        "message": "Admin access granted",
        "user_email": user['email'],
        "roles": user['roles'],
    }


# Support team-only endpoint
@router.get("/support-only")
async def support_only(user: Dict[str, Any] = Depends(require_role("support_team"))):
    """Support team-only endpoint. Returns 403 if user doesn't have support_team role."""
    return {
        "message": "Support team access granted",
        "user_email": user['email'],
        "roles": user['roles'],
    }


# Moderator-only endpoint
@router.get("/moderator-only")
async def moderator_only(user: Dict[str, Any] = Depends(require_role("moderator"))):
    """Moderator-only endpoint. Returns 403 if user doesn't have moderator role."""
    return {
        "message": "Moderator access granted",
        "user_email": user['email'],
        "roles": user['roles'],
    }


# Admin or Moderator endpoint (using require_any_role)
@router.get("/admin-or-moderator")
async def admin_or_moderator(
    user: Dict[str, Any] = Depends(require_any_role(["admin", "moderator"]))
):
    """Endpoint that requires either admin or moderator role."""
    return {
        "message": "Admin or Moderator access granted",
        "user_email": user['email'],
        "roles": user['roles'],
    }


# Admin or Support Team endpoint
@router.get("/admin-or-support")
async def admin_or_support(
    user: Dict[str, Any] = Depends(require_any_role(["admin", "support_team"]))
):
    """Endpoint that requires either admin or support_team role."""
    return {
        "message": "Admin or Support Team access granted",
        "user_email": user['email'],
        "roles": user['roles'],
    }


# Custom role requirement (example with dynamic role)
@router.get("/custom-role/{role_name}")
async def custom_role_endpoint(
    role_name: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Example: Check arbitrary role requirement (demonstrates require_role factory)."""
    # If you want to require a custom role dynamically, create the dependency first
    async def require_custom(u: Dict[str, Any] = Depends(require_role(role_name))):
        return u
    
    # This would need to be called separately in production
    return {
        "message": f"To access {role_name}-only content, use require_role('{role_name}')",
        "requested_role": role_name,
        "user_email": user['email'],
    }


# Optional auth with role info (if authenticated)
@router.get("/optional-with-roles")
async def optional_auth_with_roles(user: Dict[str, Any] = Depends(get_current_user_optional)):
    """Optional auth endpoint that shows roles if user is authenticated."""
    if user:
        roles = user.get('roles', [])
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
