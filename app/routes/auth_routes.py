"""
Authentication routes - wrapper around Supabase.

Frontend handles complete Supabase OAuth flow.
Backend provides utility endpoints.
"""

from fastapi import APIRouter, HTTPException, Response, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.dependencies import get_current_user, get_current_user_optional, build_user_response
from app.database import get_supabase_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


class ProfileUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    college: Optional[str] = None
    graduation_year: Optional[str] = None
    branch: Optional[str] = None
    codeforces_handle: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("/me")
async def me(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user data including profile fields from public.users."""
    try:
        client = get_supabase_client()
        user_id = user["id"]
        
        # Query public.users table for profile fields
        res = client.table("users").select(
            "college, graduation_year, branch, codeforces_id, social_links, metadata, pro_subscription, purchased_courses"
        ).eq("id", user_id).execute()
        
        db_user = res.data[0] if res.data and len(res.data) > 0 else {}
        
        # Merge profile fields into user dict
        return {
            **user,
            "college": db_user.get("college") or "",
            "graduation_year": db_user.get("graduation_year") or "",
            "branch": db_user.get("branch") or "",
            "codeforces_handle": db_user.get("codeforces_id") or "",
            "social_links": db_user.get("social_links") or {},
            "metadata": db_user.get("metadata") or {},
            "pro_subscription": db_user.get("pro_subscription") or {},
            "purchased_courses": db_user.get("purchased_courses") or {},
        }
    except Exception as e:
        logger.error(f"Error fetching extended profile for user {user['id']}: {str(e)}")
        # Fallback to standard user response if table query fails
        return {
            **user,
            "college": "",
            "graduation_year": "",
            "branch": "",
            "codeforces_handle": "",
            "social_links": {},
            "metadata": {},
            "pro_subscription": {},
            "purchased_courses": {},
        }


@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdateSchema,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Update current user profile details in auth.users and public.users."""
    try:
        client = get_supabase_client()
        user_id = user["id"]
        
        # 1. Update full_name in Supabase Auth user_metadata if provided
        if profile_data.full_name is not None:
            auth_user_resp = client.auth.admin.get_user_by_id(user_id)
            auth_user = auth_user_resp.user if hasattr(auth_user_resp, 'user') else auth_user_resp
            existing_meta = auth_user.user_metadata or {}
            
            updated_meta = {
                **existing_meta,
                "full_name": profile_data.full_name,
                "name": profile_data.full_name
            }
            client.auth.admin.update_user_by_id(user_id, {"user_metadata": updated_meta})
            
        # 2. Update public.users table for profile fields
        db_payload = {}
        if profile_data.college is not None:
            db_payload["college"] = profile_data.college
        if profile_data.graduation_year is not None:
            db_payload["graduation_year"] = profile_data.graduation_year
        if profile_data.branch is not None:
            db_payload["branch"] = profile_data.branch
        if profile_data.codeforces_handle is not None:
            db_payload["codeforces_id"] = profile_data.codeforces_handle
            
        # Get existing social_links & metadata to merge updates
        existing_res = client.table("users").select("social_links, metadata").eq("id", user_id).execute()
        existing_row = existing_res.data[0] if existing_res.data and len(existing_res.data) > 0 else {}
        
        if profile_data.social_links is not None:
            current_socials = existing_row.get("social_links") or {}
            current_socials.update(profile_data.social_links)
            db_payload["social_links"] = current_socials
            
        if profile_data.metadata is not None:
            current_meta = existing_row.get("metadata") or {}
            current_meta.update(profile_data.metadata)
            db_payload["metadata"] = current_meta
            
        if db_payload or profile_data.full_name is not None:
            # Upsert the row in public.users to ensure it exists
            db_payload["id"] = user_id
            db_payload["user_email"] = user["email"]
            client.table("users").upsert(db_payload).execute()
            
        # 3. Retrieve updated auth details and db details to return
        updated_auth_resp = client.auth.admin.get_user_by_id(user_id)
        updated_auth_user = updated_auth_resp.user if hasattr(updated_auth_resp, 'user') else updated_auth_resp
        clean_user = build_user_response(updated_auth_user)
        
        # Query public.users again to get current fields
        res = client.table("users").select(
            "college, graduation_year, branch, codeforces_id, social_links, metadata, pro_subscription, purchased_courses"
        ).eq("id", user_id).execute()
        db_user = res.data[0] if res.data and len(res.data) > 0 else {}
        
        return {
            **clean_user,
            "college": db_user.get("college") or "",
            "graduation_year": db_user.get("graduation_year") or "",
            "branch": db_user.get("branch") or "",
            "codeforces_handle": db_user.get("codeforces_id") or "",
            "social_links": db_user.get("social_links") or {},
            "metadata": db_user.get("metadata") or {},
            "pro_subscription": db_user.get("pro_subscription") or {},
            "purchased_courses": db_user.get("purchased_courses") or {},
        }
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update profile: {str(e)}"
        )


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
