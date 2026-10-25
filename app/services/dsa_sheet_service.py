from typing import List, Optional
from app.database import get_supabase_client
from app.schemas.dsa_sheet import DSASheetCreate, DSASheetUpdate
from app.utils.cache import cache_manager
from fastapi import HTTPException

def get_sheets(
    include_inactive: bool = False, 
    limit: Optional[int] = None, 
    user_id: Optional[str] = None, 
    token: str = None
) -> List[dict]:
    """
    Fetch DSA sheets from the database with problem counts and user solved counts.
    If include_inactive is true, returns all sheets (admin use).
    Otherwise, returns only is_active=True.
    """
    cache_key = f"dsa_sheets:user:{user_id}:{include_inactive}:{limit}" if user_id else f"dsa_sheets:all:{include_inactive}:{limit}"
    cached_val = cache_manager.get(cache_key)
    if cached_val is not None:
        return cached_val

    client = get_supabase_client(jwt_token=token)
    query = client.table("dsa_sheets").select("*")
    
    if not include_inactive:
        query = query.eq("is_active", True)
        
    response = query.order("created_at", desc=True).execute()
    sheets = response.data or []
    
    # If user_id is provided, fetch user's solved problem IDs & slugs to compute solved_problems count
    solved_identifiers = set()
    if user_id:
        try:
            import uuid
            states_res = client.table("user_asset_states").select("asset_id").eq("user_id", str(user_id)).eq("status", "done").eq("asset_type", "problem").execute()
            done_asset_ids = [r["asset_id"] for r in (states_res.data or []) if r.get("asset_id")]
            
            valid_uuids = []
            for aid in done_asset_ids:
                aid_str = str(aid).strip()
                solved_identifiers.add(aid_str)
                try:
                    uuid.UUID(aid_str)
                    valid_uuids.append(aid_str)
                except ValueError:
                    pass

            if valid_uuids:
                for i in range(0, len(valid_uuids), 100):
                    batch = valid_uuids[i:i + 100]
                    prob_res = client.table("practice_problems").select("id, slug").in_("id", batch).execute()
                    for p in (prob_res.data or []):
                        if p.get("id"):
                            solved_identifiers.add(str(p["id"]))
                        if p.get("slug"):
                            solved_identifiers.add(str(p["slug"]))
        except Exception:
            pass

    for sheet in sheets:
        sheet_json = sheet.get("sheet_json") or {}
        topics = sheet_json.get("topics", [])
        total_topics = len(topics)
        total_problems = 0
        solved_count = 0
        for topic in topics:
            for step in topic.get("steps", []):
                for prob in step.get("problems", []):
                    total_problems += 1
                    pid = str(prob.get("problem_id") or "").strip()
                    if pid and pid in solved_identifiers:
                        solved_count += 1
        
        sheet["total_topics"] = total_topics
        sheet["total_problems"] = total_problems
        sheet["solved_problems"] = solved_count
        # Purge sheet_json to make the response extremely lightweight
        sheet.pop("sheet_json", None)
        
    if limit is not None and limit > 0:
        sheets = sheets[:limit]

    ttl = 86400
    cache_manager.set(cache_key, sheets, ttl=ttl, namespace="sheets")
    return sheets

def get_sheet_by_id(sheet_id: str, include_inactive: bool = False, token: str = None) -> Optional[dict]:
    """
    Fetch a single sheet by id. Admin can see inactive sheets.
    """
    cache_key = f"dsa_sheet:{sheet_id}:{include_inactive}"
    cached_val = cache_manager.get(cache_key)
    if cached_val is not None:
        return cached_val

    client = get_supabase_client(jwt_token=token)
    query = client.table("dsa_sheets").select("*").eq("id", sheet_id)
    
    if not include_inactive:
        query = query.eq("is_active", True)
        
    # Using limit(1) instead of single() to avoid PGRST116 error when 0 rows exist
    response = query.limit(1).execute()
    result = response.data[0] if response.data else None
    if result:
        cache_manager.set(cache_key, result, ttl=86400, namespace="sheets")
    return result

def create_sheet(sheet_data: DSASheetCreate, token: str = None) -> dict:
    """
    Creates a new DSA sheet in the database.
    Ensures id uniqueness and atomic structure.
    """
    client = get_supabase_client(jwt_token=token)
    
    # Supabase.insert() returns a list of inserted rows
    response = client.table("dsa_sheets") \
        .insert(sheet_data.dict()) \
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create DSA sheet")
    
    cache_manager.invalidate_namespace("sheets")
    return response.data[0]

def update_sheet(sheet_id: str, update_data: DSASheetUpdate, token: str = None) -> dict:
    """
    Update an existing sheet.
    Supports partial updates by excluding fields not provided in request.
    """
    client = get_supabase_client(jwt_token=token)
    
    # Use exclude_unset=True to only update provided fields
    data = update_data.dict(exclude_unset=True)
    if not data:
        # If no fields are provided, maybe just return the current sheet
        return get_sheet_by_id(sheet_id, include_inactive=True, token=token)
        
    data["updated_at"] = "now()"
    
    response = client.table("dsa_sheets") \
        .update(data) \
        .eq("id", sheet_id) \
        .eq("is_active", True) \
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Sheet with id {sheet_id} not found or inactive")
    
    cache_manager.invalidate_namespace("sheets")
    return response.data[0]

def soft_delete_sheet(sheet_id: str, token: str = None) -> bool:
    """
    Perform a soft delete by setting is_active to false.
    """
    client = get_supabase_client(jwt_token=token)
    
    response = client.table("dsa_sheets") \
        .update({"is_active": False}) \
        .eq("id", sheet_id) \
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Sheet with id {sheet_id} not found")
        
    cache_manager.invalidate_namespace("sheets")
    return True

def get_sheet_problems(sheet_id: str, token: str = None) -> List[dict]:
    """
    Fetch all practice problems detailed info for a specific DSA sheet.
    """
    cache_key = f"dsa_sheet_problems:{sheet_id}"
    cached_val = cache_manager.get(cache_key)
    if cached_val is not None:
        return cached_val

    sheet = get_sheet_by_id(sheet_id, include_inactive=False, token=token)
    if not sheet:
        raise HTTPException(status_code=404, detail="Sheet not found")
        
    problem_slugs = set()
    sheet_json = sheet.get("sheet_json", {})
    for topic in sheet_json.get("topics", []):
        for step in topic.get("steps", []):
            for prob in step.get("problems", []):
                if prob.get("problem_id"):
                    problem_slugs.add(str(prob["problem_id"]).strip())
                    
    if not problem_slugs:
        return []
        
    client = get_supabase_client(jwt_token=token)
    cols = "id,slug,title,difficulty,platform,problem_url,attributes,is_active,created_at,updated_at"
    
    # Batch query unique slugs in chunks of 50 to prevent URI length overflows
    slug_list = list(problem_slugs)
    all_problems = []
    for i in range(0, len(slug_list), 50):
        batch = slug_list[i:i + 50]
        response = client.table("practice_problems") \
            .select(cols) \
            .in_("slug", batch) \
            .eq("is_active", True) \
            .execute()
        all_problems.extend(response.data or [])
        
    cache_manager.set(cache_key, all_problems, ttl=86400, namespace="sheets")
    return all_problems
