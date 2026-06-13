from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.models.user_preferences import RoadmapUserInput
from app.controllers.roadmap_controller import (
    generate_roadmap_handler,
    list_roadmaps_handler,
    get_active_roadmap_handler,
    get_roadmap_by_id_handler,
    activate_roadmap_handler,
    rename_roadmap_handler,
    delete_roadmap_handler
)
from app.dependencies import get_current_user_with_token, verify_admin_token, require_role_with_token
from app.database import get_supabase_client

router = APIRouter(
    prefix="/roadmap",
    tags=["Roadmap Generation"]
)

@router.post("/generate")
async def generate_roadmap_endpoint(
    prefs: RoadmapUserInput,
    auth_data: dict = Depends(get_current_user_with_token)
):
    user_id = auth_data["user"]["id"]
    token = auth_data["token"]
    return await generate_roadmap_handler(user_id, prefs, token)

@router.get("/")
def list_roadmaps_endpoint(
    auth_data: dict = Depends(get_current_user_with_token)
):
    user_id = auth_data["user"]["id"]
    token = auth_data["token"]
    return list_roadmaps_handler(user_id, token)

@router.get("/active")
def get_active_roadmap_endpoint(
    auth_data: dict = Depends(get_current_user_with_token)
):
    user_id = auth_data["user"]["id"]
    token = auth_data["token"]
    return get_active_roadmap_handler(user_id, token)

@router.get("/{roadmap_id}")
def get_roadmap_by_id_endpoint(
    roadmap_id: str,
    auth_data: dict = Depends(get_current_user_with_token)
):
    user_id = auth_data["user"]["id"]
    token = auth_data["token"]
    return get_roadmap_by_id_handler(user_id, roadmap_id, token)

@router.post("/{roadmap_id}/activate")
def activate_roadmap_endpoint(
    roadmap_id: str,
    auth_data: dict = Depends(get_current_user_with_token)
):
    user_id = auth_data["user"]["id"]
    token = auth_data["token"]
    return activate_roadmap_handler(user_id, roadmap_id, token)

class RenameRoadmapRequest(BaseModel):
    title: str

@router.post("/{roadmap_id}/rename")
def rename_roadmap_endpoint(
    roadmap_id: str,
    req: RenameRoadmapRequest,
    auth_data: dict = Depends(get_current_user_with_token)
):
    user_id = auth_data["user"]["id"]
    token = auth_data["token"]
    return rename_roadmap_handler(user_id, roadmap_id, req.title, token)

@router.delete("/{roadmap_id}")
def delete_roadmap_endpoint(
    roadmap_id: str,
    auth_data: dict = Depends(get_current_user_with_token)
):
    user_id = auth_data["user"]["id"]
    token = auth_data["token"]
    return delete_roadmap_handler(user_id, roadmap_id, token)


# --- Admin Router ---
admin_router = APIRouter(
    prefix="/admin/roadmaps",
    tags=["Roadmaps (Admin)"]
)

@admin_router.get("")
@admin_router.get("/", include_in_schema=False)
def list_roadmaps_admin(auth_data = Depends(require_role_with_token("admin"))):
    """
    List all generated roadmaps across all users (Admin only).
    """
    client = get_supabase_client(auth_data["token"])
    
    # 1. Fetch all non-deleted roadmaps
    roadmaps_res = client.table("user_roadmaps").select("*").eq("is_deleted", False).order("created_at", desc=True).execute()
    roadmaps = roadmaps_res.data or []
    
    # 2. Fetch users to map user_id to email & full name
    users_res = client.table("users").select("id, user_email, metadata").execute()
    users_data = users_res.data or []
    user_map = {}
    for u in users_data:
        metadata = u.get("metadata") or {}
        user_map[u["id"]] = {
            "email": u.get("user_email") or "",
            "full_name": metadata.get("full_name") or metadata.get("name") or ""
        }
        
    # 3. Merge user info
    for r in roadmaps:
        u_id = r.get("user_id")
        r["user"] = user_map.get(u_id, {"email": "unknown@crackdsa.com", "full_name": "Unknown User"})
        
    return roadmaps

@admin_router.get("/{roadmap_id}")
@admin_router.get("/{roadmap_id}/", include_in_schema=False)
def get_roadmap_admin(roadmap_id: str, auth_data = Depends(require_role_with_token("admin"))):
    """
    Retrieve details of a specific roadmap by ID (Admin only).
    """
    client = get_supabase_client(auth_data["token"])
    res = client.table("user_roadmaps").select("*").eq("id", roadmap_id).eq("is_deleted", False).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Roadmap not found")
        
    roadmap = res.data[0]
    
    # Attach user details
    u_res = client.table("users").select("id, user_email, metadata").eq("id", roadmap["user_id"]).execute()
    if u_res.data:
        u = u_res.data[0]
        metadata = u.get("metadata") or {}
        roadmap["user"] = {
            "email": u.get("user_email") or "",
            "full_name": metadata.get("full_name") or metadata.get("name") or ""
        }
    else:
        roadmap["user"] = {"email": "unknown@crackdsa.com", "full_name": "Unknown User"}
        
    return roadmap

class AdminUpdateRoadmapRequest(BaseModel):
    title: str
    is_active: bool
    structure: Dict[str, Any]
    user_input: Optional[Dict[str, Any]] = None

@admin_router.put("/{roadmap_id}")
@admin_router.put("/{roadmap_id}/", include_in_schema=False)
def update_roadmap_admin(
    roadmap_id: str,
    req: AdminUpdateRoadmapRequest,
    auth_data = Depends(require_role_with_token("admin"))
):
    """
    Update details (title, active status, structural JSON) of a specific roadmap (Admin only).
    """
    client = get_supabase_client(auth_data["token"])
    
    check_res = client.table("user_roadmaps").select("id, user_id").eq("id", roadmap_id).eq("is_deleted", False).execute()
    if not check_res.data:
        raise HTTPException(status_code=404, detail="Roadmap not found")
        
    user_id = check_res.data[0]["user_id"]
    
    if req.is_active:
        client.table("user_roadmaps").update({"is_active": False}).eq("user_id", user_id).execute()
        
    payload = {
        "title": req.title,
        "is_active": req.is_active,
        "structure": req.structure,
    }
    if req.user_input is not None:
        payload["user_input"] = req.user_input
        
    res = client.table("user_roadmaps").update(payload).eq("id", roadmap_id).execute()
    if not res.data:
         raise HTTPException(status_code=400, detail="Failed to update roadmap")
         
    return res.data[0]

@admin_router.delete("/{roadmap_id}")
@admin_router.delete("/{roadmap_id}/", include_in_schema=False)
def delete_roadmap_admin(roadmap_id: str, auth_data = Depends(require_role_with_token("admin"))):
    """
    Delete (soft-delete) a specific roadmap (Admin only).
    """
    client = get_supabase_client(auth_data["token"])
    
    check_res = client.table("user_roadmaps").select("id, user_id, is_active").eq("id", roadmap_id).eq("is_deleted", False).execute()
    if not check_res.data:
        raise HTTPException(status_code=404, detail="Roadmap not found")
        
    user_id = check_res.data[0]["user_id"]
    was_active = check_res.data[0]["is_active"]
    
    client.table("user_roadmaps").update({"is_deleted": True, "is_active": False}).eq("id", roadmap_id).execute()
    
    if was_active:
        remaining = client.table("user_roadmaps").select("id").eq("user_id", user_id).eq("is_deleted", False).order("created_at", desc=True).limit(1).execute()
        if remaining.data:
            client.table("user_roadmaps").update({"is_active": True}).eq("id", remaining.data[0]["id"]).execute()
            
    return {"status": "success"}
