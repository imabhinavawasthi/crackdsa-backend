from typing import List, Optional
from app.database import get_supabase_client
from app.schemas.dsa_sheet import DSASheetCreate, DSASheetUpdate
from fastapi import HTTPException

def get_sheets(include_inactive: bool = False, token: str = None) -> List[dict]:
    """
    Fetch DSA sheets from the database.
    If include_inactive is true, returns all sheets (admin use).
    Otherwise, returns only is_active=True.
    """
    client = get_supabase_client(jwt_token=token)
    query = client.table("dsa_sheets").select("*")
    
    if not include_inactive:
        query = query.eq("is_active", True)
        
    response = query.order("created_at", desc=True).execute()
    return response.data

def get_sheet_by_id(sheet_id: str, include_inactive: bool = False, token: str = None) -> Optional[dict]:
    """
    Fetch a single sheet by id. Admin can see inactive sheets.
    """
    client = get_supabase_client(jwt_token=token)
    query = client.table("dsa_sheets").select("*").eq("id", sheet_id)
    
    if not include_inactive:
        query = query.eq("is_active", True)
        
    # Using limit(1) instead of single() to avoid PGRST116 error when 0 rows exist
    response = query.limit(1).execute()
    
    return response.data[0] if response.data else None

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
        
    return True
