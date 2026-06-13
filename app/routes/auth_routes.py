"""
Authentication routes - wrapper around Supabase.

Frontend handles complete Supabase OAuth flow.
Backend provides utility endpoints.
"""

from fastapi import APIRouter, HTTPException, Response, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.dependencies import get_current_user, get_current_user_optional, get_current_user_with_token, build_user_response
from app.database import get_supabase_client
from app.config import settings
import logging
import httpx

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


class RefreshTokenSchema(BaseModel):
    refresh_token: str

@router.get("/me")
async def me(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user data including profile fields from public.users."""
    try:
        client = get_supabase_client()  # Admin client (RLS-bypass)
        user_id = user["id"]
        
        # Query public.users table for profile fields by ID
        res = client.table("users").select(
            "id, college, graduation_year, branch, codeforces_id, social_links, metadata, pro_subscription, purchased_courses"
        ).eq("id", user_id).execute()
        
        db_user = res.data[0] if res.data and len(res.data) > 0 else {}
        
        # Self-healing: if not found by ID, search by user_email
        if not db_user:
            email_res = client.table("users").select(
                "id, college, graduation_year, branch, codeforces_id, social_links, metadata, pro_subscription, purchased_courses"
            ).eq("user_email", user["email"]).execute()
            if email_res.data:
                db_user = email_res.data[0]
                existing_id = db_user["id"]
                # Align the ID in the database to match Supabase Auth UUID
                client.table("users").update({"id": user_id}).eq("id", existing_id).execute()
        
        # Merge profile fields into user dict
        response_data = {
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
        
        # Override full_name if it is stored in database metadata
        db_metadata = db_user.get("metadata") or {}
        if "full_name" in db_metadata:
            response_data["full_name"] = db_metadata["full_name"]
            
        return response_data
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
    auth_data: Dict[str, Any] = Depends(get_current_user_with_token)
):
    """Update current user profile details in public.users."""
    try:
        user = auth_data["user"]
        token = auth_data["token"]
        user_id = user["id"]
        
        # Admin client for db operations to bypass RLS/mismatch; token client for auth checking
        admin_client = get_supabase_client()
        
        # 1. Update public.users table for profile fields
        db_payload = {}
        if profile_data.college is not None:
            db_payload["college"] = profile_data.college
        if profile_data.graduation_year is not None:
            db_payload["graduation_year"] = profile_data.graduation_year
        if profile_data.branch is not None:
            db_payload["branch"] = profile_data.branch
        if profile_data.codeforces_handle is not None:
            db_payload["codeforces_id"] = profile_data.codeforces_handle
            
        # Get existing record by email (admin client) to prevent user_email duplicate key violations
        existing_res = admin_client.table("users").select("id, social_links, metadata").eq("user_email", user["email"]).execute()
        
        # Fallback search by ID if not found by email
        if not existing_res.data:
            existing_res = admin_client.table("users").select("id, social_links, metadata").eq("id", user_id).execute()
            
        existing_row = existing_res.data[0] if existing_res.data and len(existing_res.data) > 0 else {}
        existing_id = existing_row.get("id")
        
        if profile_data.social_links is not None:
            current_socials = existing_row.get("social_links") or {}
            current_socials.update(profile_data.social_links)
            db_payload["social_links"] = current_socials
            
        # Manage metadata (merge full_name and other metadata updates)
        current_meta = existing_row.get("metadata") or {}
        has_metadata_updates = False
        
        if profile_data.full_name is not None:
            current_meta["full_name"] = profile_data.full_name
            has_metadata_updates = True
            
        if profile_data.metadata is not None:
            current_meta.update(profile_data.metadata)
            has_metadata_updates = True
            
        if has_metadata_updates:
            db_payload["metadata"] = current_meta
            
        if db_payload:
            if existing_id:
                # If the ID in the database is different from user_id, align it
                if existing_id != user_id:
                    db_payload["id"] = user_id
                
                admin_client.table("users").update(db_payload).eq("id", existing_id).execute()
            else:
                db_payload["id"] = user_id
                db_payload["user_email"] = user["email"]
                admin_client.table("users").insert(db_payload).execute()
            
        # 2. Retrieve auth details and db details to return
        clean_user = user
        
        # Query public.users again to get current fields (admin client)
        res = admin_client.table("users").select(
            "college, graduation_year, branch, codeforces_id, social_links, metadata, pro_subscription, purchased_courses"
        ).eq("id", user_id).execute()
        db_user = res.data[0] if res.data and len(res.data) > 0 else {}
        
        response_data = {
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
        
        # Override full_name if it is stored in database metadata
        db_metadata = db_user.get("metadata") or {}
        if "full_name" in db_metadata:
            response_data["full_name"] = db_metadata["full_name"]
            
        return response_data
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


@router.post("/refresh")
async def refresh_token(data: RefreshTokenSchema):
    """Silently refresh a user's session using their refresh token."""
    try:
        client = get_supabase_client()
        # Supabase Python client auth.refresh_session returns an AuthResponse
        resp = client.auth.refresh_session(data.refresh_token)
        session = resp.session
        
        if not session:
            raise ValueError("No session returned from Supabase")
            
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expires_in": session.expires_in
        }
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )
