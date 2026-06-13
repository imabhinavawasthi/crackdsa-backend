from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from app.models.user_preferences import RoadmapUserInput
from app.models.roadmap import RoadmapStructure
from app.utils.problem_loader import get_relevant_problems_for_ai
from app.services.ai_service import generate_roadmap_from_ai
from app.database import get_supabase_client
import json

async def generate_and_save_roadmap(user_id: str, prefs: RoadmapUserInput, token: str) -> dict:
    problems = get_relevant_problems_for_ai(
        strong_topics=prefs.strong_topics, 
        weak_topics=prefs.weak_topics
    )
    
    # 1. Generate with AI
    roadmap = await generate_roadmap_from_ai(prefs=prefs, problems=problems)
    
    # 2. Database Insert
    client = get_supabase_client(token)
    
    title = f"{prefs.target_role} Prep - {prefs.target_company_tier}"
    
    # Deactivate other roadmaps first
    client.table("user_roadmaps").update({"is_active": False}).eq("user_id", user_id).execute()
    
    # Insert new roadmap
    payload = {
        "user_id": user_id,
        "title": title,
        "user_input": prefs.model_dump(),
        "structure": roadmap.model_dump(),
        "is_active": True,
        "is_deleted": False,
        "metadata": {}
    }
    
    res = client.table("user_roadmaps").insert(payload).execute()
    return res.data[0] if res.data else {}

def list_user_roadmaps(user_id: str, token: str) -> List[Dict[str, Any]]:
    client = get_supabase_client(token)
    res = client.table("user_roadmaps").select("id, title, is_active, created_at").eq("user_id", user_id).eq("is_deleted", False).order("created_at", desc=True).execute()
    return res.data

def get_active_roadmap(user_id: str, token: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client(token)
    res = client.table("user_roadmaps").select("*").eq("user_id", user_id).eq("is_active", True).eq("is_deleted", False).execute()
    
    if not res.data:
        return None
        
    roadmap_data = res.data[0]
    
    # Fetch user asset states to dynamically overlay progress
    states_res = client.table("user_asset_states").select("asset_id, status").eq("user_id", user_id).execute()
    completed_assets = {s["asset_id"] for s in states_res.data if s["status"] == "done"}
    
    structure = roadmap_data["structure"]
    
    found_current = False
    
    for phase in structure.get("phases", []):
        for topic in phase.get("topics", []):
            for item in topic.get("items", []):
                if item["id"] in completed_assets:
                    item["status"] = "completed"
                else:
                    if not found_current:
                        item["status"] = "current"
                        found_current = True
                    else:
                        item["status"] = "locked"
                        
    return roadmap_data

def get_roadmap_by_id(user_id: str, roadmap_id: str, token: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client(token)
    res = client.table("user_roadmaps").select("*").eq("user_id", user_id).eq("id", roadmap_id).eq("is_deleted", False).execute()
    
    if not res.data:
        return None
        
    roadmap_data = res.data[0]
    
    # Fetch user asset states to dynamically overlay progress
    states_res = client.table("user_asset_states").select("asset_id, status").eq("user_id", user_id).execute()
    completed_assets = {s["asset_id"] for s in states_res.data if s["status"] == "done"}
    
    structure = roadmap_data["structure"]
    
    found_current = False
    
    for phase in structure.get("phases", []):
        for topic in phase.get("topics", []):
            for item in topic.get("items", []):
                if item["id"] in completed_assets:
                    item["status"] = "completed"
                else:
                    if not found_current:
                        item["status"] = "current"
                        found_current = True
                    else:
                        item["status"] = "locked"
                        
    return roadmap_data

def activate_roadmap(user_id: str, roadmap_id: str, token: str):
    client = get_supabase_client(token)
    # Deactivate all
    client.table("user_roadmaps").update({"is_active": False}).eq("user_id", user_id).execute()
    # Activate selected
    client.table("user_roadmaps").update({"is_active": True}).eq("id", roadmap_id).eq("user_id", user_id).execute()
    return {"status": "success"}

def rename_roadmap(user_id: str, roadmap_id: str, new_title: str, token: str):
    client = get_supabase_client(token)
    client.table("user_roadmaps").update({"title": new_title}).eq("id", roadmap_id).eq("user_id", user_id).execute()
    return {"status": "success"}

def delete_roadmap(user_id: str, roadmap_id: str, token: str):
    client = get_supabase_client(token)
    
    # Check if the roadmap being deleted is active
    res = client.table("user_roadmaps").select("is_active").eq("id", roadmap_id).eq("user_id", user_id).execute()
    was_active = False
    if res.data and res.data[0].get("is_active"):
        was_active = True
        
    # Soft delete
    client.table("user_roadmaps").update({"is_deleted": True, "is_active": False}).eq("id", roadmap_id).eq("user_id", user_id).execute()
    
    # Auto-activate the most recent one if we just deleted the active one
    if was_active:
        remaining = client.table("user_roadmaps").select("id").eq("user_id", user_id).eq("is_deleted", False).order("created_at", desc=True).limit(1).execute()
        if remaining.data:
            client.table("user_roadmaps").update({"is_active": True}).eq("id", remaining.data[0]["id"]).execute()
            
    return {"status": "success"}
