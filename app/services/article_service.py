from typing import List, Optional
from app.database import get_supabase_client
from app.schemas.article import ArticleCreate, ArticleUpdate
from fastapi import HTTPException
from uuid import UUID

def get_articles(include_inactive: bool = False, token: str = None) -> List[dict]:
    """
    Fetch articles from the database.
    If include_inactive is true, returns all active articles including drafts (admin use).
    Otherwise, returns only is_published=True AND is_active=True (public use).
    """
    client = get_supabase_client(jwt_token=token)
    query = client.table("articles").select("*")
    
    if not include_inactive:
        query = query.eq("is_published", True).eq("is_active", True)
    else:
        query = query.eq("is_active", True)
        
    response = query.order("created_at", desc=True).execute()
    return response.data

def get_article_by_id(article_id: UUID, include_inactive: bool = False, token: str = None) -> Optional[dict]:
    """
    Fetch a single article by its UUID.
    """
    client = get_supabase_client(jwt_token=token)
    query = client.table("articles").select("*").eq("id", str(article_id))
    
    if not include_inactive:
        query = query.eq("is_published", True).eq("is_active", True)
    else:
        query = query.eq("is_active", True)
        
    response = query.limit(1).execute()
    return response.data[0] if response.data else None

def get_article_by_slug(slug: str, include_inactive: bool = False, token: str = None) -> Optional[dict]:
    """
    Fetch a single article by its unique slug.
    """
    client = get_supabase_client(jwt_token=token)
    query = client.table("articles").select("*").eq("slug", slug)
    
    if not include_inactive:
        query = query.eq("is_published", True).eq("is_active", True)
    else:
        query = query.eq("is_active", True)
        
    response = query.limit(1).execute()
    return response.data[0] if response.data else None

def create_article(article_data: ArticleCreate, token: str = None) -> dict:
    """
    Inserts a new article into the database.
    """
    client = get_supabase_client(jwt_token=token)
    
    response = client.table("articles") \
        .insert(article_data.dict()) \
        .execute()
        
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create article")
        
    return response.data[0]

def update_article(article_id: UUID, update_data: ArticleUpdate, token: str = None) -> dict:
    """
    Update an existing article.
    Supports partial updates.
    """
    client = get_supabase_client(jwt_token=token)
    
    data = update_data.dict(exclude_unset=True)
    if not data:
        return get_article_by_id(article_id, include_inactive=True, token=token)
        
    data["updated_at"] = "now()"
    
    response = client.table("articles") \
        .update(data) \
        .eq("id", str(article_id)) \
        .eq("is_active", True) \
        .execute()
        
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Article with id {article_id} not found or inactive")
        
    return response.data[0]

def soft_delete_article(article_id: UUID, token: str = None) -> bool:
    """
    Perform a soft delete by setting is_active to false.
    """
    client = get_supabase_client(jwt_token=token)
    
    response = client.table("articles") \
        .update({"is_active": False}) \
        .eq("id", str(article_id)) \
        .execute()
        
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Article with id {article_id} not found")
        
    return True
