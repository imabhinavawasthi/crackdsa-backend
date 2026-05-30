from typing import List, Optional
from app.database import get_supabase_client
from app.schemas.practice_problem import PracticeProblemCreate, PracticeProblemUpdate
from fastapi import HTTPException
from uuid import UUID

def get_practice_problems(include_inactive: bool = False, token: str = None) -> List[dict]:
    """
    Fetch practice problems from the database.
    If include_inactive is true, returns all problems (admin use).
    Otherwise, returns only is_active=True.
    """
    client = get_supabase_client(jwt_token=token)
    query = client.table("practice_problems").select("*")
    
    if not include_inactive:
        query = query.eq("is_active", True)
        
    response = query.order("created_at", desc=True).execute()
    return response.data

def get_practice_problem_by_id(problem_id: UUID, include_inactive: bool = False, token: str = None) -> Optional[dict]:
    """
    Fetch a single practice problem by its UUID.
    """
    client = get_supabase_client(jwt_token=token)
    query = client.table("practice_problems").select("*").eq("id", str(problem_id))
    
    if not include_inactive:
        query = query.eq("is_active", True)
        
    response = query.limit(1).execute()
    return response.data[0] if response.data else None

def get_practice_problem_by_slug(slug: str, include_inactive: bool = False, token: str = None) -> Optional[dict]:
    """
    Fetch a single practice problem by its unique slug.
    """
    client = get_supabase_client(jwt_token=token)
    query = client.table("practice_problems").select("*").eq("slug", slug)
    
    if not include_inactive:
        query = query.eq("is_active", True)
        
    response = query.limit(1).execute()
    return response.data[0] if response.data else None

def create_practice_problem(problem_data: PracticeProblemCreate, token: str = None) -> dict:
    """
    Inserts a new practice problem into the database.
    """
    client = get_supabase_client(jwt_token=token)
    
    response = client.table("practice_problems") \
        .insert(problem_data.dict()) \
        .execute()
        
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create practice problem")
        
    return response.data[0]

def update_practice_problem(problem_id: UUID, update_data: PracticeProblemUpdate, token: str = None) -> dict:
    """
    Update an existing practice problem.
    Supports partial updates.
    """
    client = get_supabase_client(jwt_token=token)
    
    data = update_data.dict(exclude_unset=True)
    if not data:
        return get_practice_problem_by_id(problem_id, include_inactive=True, token=token)
        
    data["updated_at"] = "now()"
    
    response = client.table("practice_problems") \
        .update(data) \
        .eq("id", str(problem_id)) \
        .eq("is_active", True) \
        .execute()
        
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Practice problem with id {problem_id} not found or inactive")
        
    return response.data[0]

def soft_delete_practice_problem(problem_id: UUID, token: str = None) -> bool:
    """
    Perform a soft delete by setting is_active to false.
    """
    client = get_supabase_client(jwt_token=token)
    
    response = client.table("practice_problems") \
        .update({"is_active": False}) \
        .eq("id", str(problem_id)) \
        .execute()
        
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Practice problem with id {problem_id} not found")
        
    return True
