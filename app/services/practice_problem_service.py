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

def get_practice_problems_basic(include_inactive: bool = False, token: str = None) -> List[dict]:
    """
    Fetch only basic details (excluding description, solutions, resources) for practice problems.
    """
    client = get_supabase_client(jwt_token=token)
    cols = "id,slug,title,difficulty,platform,problem_url,attributes,is_active,created_at,updated_at"
    query = client.table("practice_problems").select(cols)
    
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

def slugify(text: str) -> str:
    """
    Converts text to a URL-friendly slug, matching frontend slugify logic.
    """
    import re
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def get_practice_problems_by_topic(topic_slug: str, token: str = None) -> List[dict]:
    """
    Fetch all active problems matching a specific topic slug.
    """
    problems = get_practice_problems_basic(include_inactive=False, token=token)
    filtered = []
    for p in problems:
        tags = p.get("attributes", {}).get("tags", []) or p.get("attributes", {}).get("topicTags", []) or []
        if any(slugify(t) == topic_slug for t in tags):
            filtered.append(p)
    return filtered

def get_practice_problems_by_company(company_slug: str, token: str = None) -> List[dict]:
    """
    Fetch all active problems matching a specific company slug.
    """
    problems = get_practice_problems_basic(include_inactive=False, token=token)
    filtered = []
    for p in problems:
        companies = p.get("attributes", {}).get("company_tags", []) or p.get("attributes", {}).get("companyTags", []) or []
        if any(slugify(c) == company_slug for c in companies):
            filtered.append(p)
    return filtered

def get_topics_summary(token: str = None) -> List[dict]:
    """
    Computes a summary of all topic tags with their active problem counts.
    """
    problems = get_practice_problems_basic(include_inactive=False, token=token)
    topics_map = {}
    
    for p in problems:
        tags = p.get("attributes", {}).get("tags", []) or p.get("attributes", {}).get("topicTags", []) or []
        diff = p.get("difficulty", "Easy")
        
        for t in tags:
            if not t:
                continue
            slug = slugify(t)
            if not slug:
                continue
                
            if slug not in topics_map:
                topics_map[slug] = {
                    "name": t,
                    "slug": slug,
                    "count": 0,
                    "easy_count": 0,
                    "medium_count": 0,
                    "hard_count": 0
                }
            
            topics_map[slug]["count"] += 1
            if diff == "Easy":
                topics_map[slug]["easy_count"] += 1
            elif diff == "Medium":
                topics_map[slug]["medium_count"] += 1
            elif diff == "Hard":
                topics_map[slug]["hard_count"] += 1
                
    # Sort topics by count descending
    return sorted(topics_map.values(), key=lambda x: x["count"], reverse=True)

def get_companies_summary(token: str = None) -> List[dict]:
    """
    Computes a summary of all company tags with their active problem counts.
    """
    problems = get_practice_problems_basic(include_inactive=False, token=token)
    companies_map = {}
    
    for p in problems:
        companies = p.get("attributes", {}).get("company_tags", []) or p.get("attributes", {}).get("companyTags", []) or []
        diff = p.get("difficulty", "Easy")
        
        for c in companies:
            if not c:
                continue
            slug = slugify(c)
            if not slug:
                continue
                
            if slug not in companies_map:
                companies_map[slug] = {
                    "name": c,
                    "slug": slug,
                    "count": 0,
                    "easy_count": 0,
                    "medium_count": 0,
                    "hard_count": 0
                }
            
            companies_map[slug]["count"] += 1
            if diff == "Easy":
                companies_map[slug]["easy_count"] += 1
            elif diff == "Medium":
                companies_map[slug]["medium_count"] += 1
            elif diff == "Hard":
                companies_map[slug]["hard_count"] += 1
                
    # Sort companies by count descending
    return sorted(companies_map.values(), key=lambda x: x["count"], reverse=True)
