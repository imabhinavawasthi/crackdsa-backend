"""
Authentication routes - wrapper around Supabase.

Frontend handles complete Supabase OAuth flow.
Backend provides utility endpoints.
"""

from fastapi import APIRouter, HTTPException, Response, Depends, status
from typing import Dict, Any, Optional
from app.dependencies import get_current_user, get_current_user_optional, get_current_user_with_token, build_user_response, get_token
from app.database import get_supabase_client
from app.config import settings
from app.schemas.user_profile import (
    UserProfileResponse,
    ProfileUpdateSchema,
    SubscriptionDetailsResponse,
    RefreshTokenSchema,
    RefreshTokenResponse,
    TokenStatusResponse,
    LogoutResponse,
)
import logging
import httpx
import time

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

oauth_router = APIRouter(
    prefix="/oauth",
    tags=["Authentication (OAuth Alias)"]
)

def _hydrate_user_profile_response(
    user: Dict[str, Any], 
    db_user: Dict[str, Any], 
    client: Any,
    is_new_user: bool = False
) -> Dict[str, Any]:
    now_epoch = int(time.time())
    
    pro_sub = db_user.get("pro_subscription") or {}
    # Support both legacy schema (is_active) and new schema (subscription_active_till_epoch)
    if "subscription_active_till_epoch" in pro_sub:
        expiry = pro_sub.get("subscription_active_till_epoch", 0)
        is_pro_active = (expiry == -1) or (expiry > now_epoch)
    else:
        is_pro_active = pro_sub.get("is_active", False)
        
    pc = db_user.get("purchased_courses") or {}
    purchased_courses = []
    if isinstance(pc, dict) and "courses" in pc and isinstance(pc["courses"], list):
        courses = pc.get("courses", [])
        for c in courses:
            purchased_courses.append({
                "course_id": c.get("course_id"),
                "course_slug": c.get("course_slug") or c.get("course_id"),
                "course_name": c.get("course_name")
            })
    elif isinstance(pc, dict):
        # Legacy mapping
        for c_id, val in pc.items():
            name = val.get("course_name", c_id) if isinstance(val, dict) else c_id
            purchased_courses.append({
                "course_id": c_id,
                "course_slug": c_id,
                "course_name": name
            })
    elif isinstance(pc, list):
        for c in pc:
            if isinstance(c, dict):
                purchased_courses.append({
                    "course_id": c.get("course_id"),
                    "course_slug": c.get("course_slug") or c.get("course_id"),
                    "course_name": c.get("course_name")
                })
            
    pro_courses = []
    if is_pro_active:
        try:
            # Query all active courses where is_pro is True
            courses_res = client.table("courses").select("id, slug, title, is_pro, is_active").eq("is_pro", True).eq("is_active", True).execute()
            if courses_res.data:
                for c in courses_res.data:
                    c_slug = c.get("slug") or c.get("id")
                    c_id = c.get("id") or c_slug
                    pro_courses.append({
                        "course_id": c_id,
                        "course_slug": c_slug,
                        "course_name": c.get("title")
                    })
        except Exception as e:
            logger.error(f"Error fetching pro subscription courses: {str(e)}")

    # Create union list of all courses they have access to, removing duplicates
    seen_course_ids = set()
    enrolled_courses = []
    for c in (purchased_courses + pro_courses):
        cid = str(c.get("course_id") or "")
        cslug = str(c.get("course_slug") or "")
        if (cid and cid not in seen_course_ids) or (cslug and cslug not in seen_course_ids):
            if cid:
                seen_course_ids.add(cid)
            if cslug:
                seen_course_ids.add(cslug)
            enrolled_courses.append(c)
            
    db_metadata = db_user.get("metadata") or {}
    # Onboarding is skipped by default now; users can edit profile details anytime in settings
    needs_onboarding = False

    response_data = {
        **user,
        "college": db_user.get("college") or "",
        "graduation_year": db_user.get("graduation_year") or "",
        "branch": db_user.get("branch") or "",
        "codeforces_handle": db_user.get("codeforces_id") or "",
        "social_links": db_user.get("social_links") or {},
        "metadata": db_metadata,
        "is_pro_active": is_pro_active,
        "pro_courses": pro_courses,
        "purchased_courses": purchased_courses,
        "enrolled_courses": enrolled_courses,
        "pro_subscription": pro_sub,
        "is_new_user": is_new_user,
        "needs_onboarding": needs_onboarding,
    }
    
    # Override full_name if it is stored in database metadata
    if "full_name" in db_metadata:
        response_data["full_name"] = db_metadata["full_name"]
        
    return response_data


@router.get("/me", response_model=UserProfileResponse)
async def me(
    user: Dict[str, Any] = Depends(get_current_user),
    token: str = Depends(get_token)
):
    """Get current authenticated user data including profile fields from public.users."""
    try:
        admin_client = get_supabase_client()  # Service/admin client guarantees RLS bypass and table healing
        client = get_supabase_client(jwt_token=token)  # Scoped user client (RLS-enabled)
        user_id = user["id"]
        is_new_user = False
        
        # Query public.users table for profile fields by ID
        res = admin_client.table("users").select(
            "id, college, graduation_year, branch, codeforces_id, social_links, metadata, pro_subscription, purchased_courses"
        ).eq("id", user_id).execute()
        
        db_user = res.data[0] if res.data and len(res.data) > 0 else {}
        
        # Self-healing: if not found by ID, search by user_email
        if not db_user:
            email_res = admin_client.table("users").select(
                "id, college, graduation_year, branch, codeforces_id, social_links, metadata, pro_subscription, purchased_courses"
            ).eq("user_email", user["email"]).execute()
            if email_res.data:
                db_user = email_res.data[0]
                existing_id = db_user["id"]
                # Align the ID in the database to match Supabase Auth UUID
                if existing_id != user_id:
                    admin_client.table("users").update({"id": user_id}).eq("id", existing_id).execute()
                    db_user["id"] = user_id
            else:
                # User does not exist in public.users -> INSERT ROW IMMEDIATELY
                logger.info(f"User {user['email']} not found in public.users. Creating default user entry.")
                new_row = {
                    "id": user_id,
                    "user_email": user["email"],
                    "college": None,
                    "graduation_year": None,
                    "branch": None,
                    "codeforces_id": None,
                    "bookmarked_problems": [],
                    "pending_problems": [],
                    "trying_problems": [],
                    "solved_problems": [],
                    "revise_problems": [],
                    "social_links": {},
                    "metadata": {
                        "full_name": user.get("full_name") or "",
                        "avatar_url": user.get("avatar_url") or "",
                        "onboarding_completed": True
                    },
                    "pro_subscription": {},
                    "purchased_courses": {}
                }
                insert_res = admin_client.table("users").insert(new_row).execute()
                db_user = insert_res.data[0] if insert_res.data else new_row
                is_new_user = True
        
        return _hydrate_user_profile_response(user, db_user, client, is_new_user=is_new_user)
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
            "is_pro_active": False,
            "pro_courses": [],
            "purchased_courses": [],
            "enrolled_courses": [],
            "pro_subscription": {},
            "is_new_user": False,
            "needs_onboarding": False,
        }


@router.get("/subscription-details", response_model=SubscriptionDetailsResponse)
async def get_subscription_details(user: Dict[str, Any] = Depends(get_current_user)):
    """Get complete subscription and course purchase details for the authenticated user."""
    try:
        client = get_supabase_client()
        user_id = user["id"]
        
        res = client.table("users").select(
            "pro_subscription, purchased_courses"
        ).eq("id", user_id).execute()
        
        if not res.data:
            return {"pro_subscription": {}, "purchased_courses": {"courses": []}}
            
        db_user = res.data[0]
        
        return {
            "pro_subscription": db_user.get("pro_subscription") or {},
            "purchased_courses": db_user.get("purchased_courses") or {"courses": []}
        }
    except Exception as e:
        logger.error(f"Error fetching subscription details for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscription details")


@router.put("/profile", response_model=UserProfileResponse)
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
        
        return _hydrate_user_profile_response(clean_user, db_user, admin_client)
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponse)
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


@oauth_router.post("/logout", response_model=LogoutResponse, include_in_schema=False)
async def oauth_logout(response: Response):
    """Alias for /api/v1/auth/logout to ensure backwards compatibility with OAuth client calls."""
    return await logout(response)


@router.get("/token-status", response_model=TokenStatusResponse)
async def token_status(user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Check if user has a valid token."""
    return {"authenticated": user is not None}


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(data: RefreshTokenSchema):
    """Silently refresh a user's session using their refresh token."""
    try:
        # Create an isolated client for token refresh to prevent session state pollution on the global client
        from supabase import create_client
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
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
