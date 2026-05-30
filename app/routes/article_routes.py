from typing import List, Optional
from fastapi import APIRouter, Depends
from app.schemas.article import Article, ArticleCreate, ArticleUpdate
from app.controllers import article_controller
from app.dependencies import require_role_with_token, get_token
from uuid import UUID

# --- Public Router ---
# General access: only list published+active articles and retrieve by ID or Slug
public_router = APIRouter(
    prefix="/articles",
    tags=["Articles (Public)"]
)

@public_router.get("", response_model=List[Article])
async def list_articles_public(token: Optional[str] = Depends(get_token)):
    """
    List all published and active articles for public discovery.
    """
    return await article_controller.list_articles_handler(include_inactive=False, token=token)

@public_router.get("/{slug_or_id}", response_model=Article)
async def get_article_public(slug_or_id: str, token: Optional[str] = Depends(get_token)):
    """
    Get a single published and active article by its UUID or unique slug.
    """
    try:
        article_id = UUID(slug_or_id)
        return await article_controller.get_article_handler(article_id, include_inactive=False, token=token)
    except ValueError:
        return await article_controller.get_article_by_slug_handler(slug_or_id, include_inactive=False, token=token)


# --- Admin Router ---
# Full CRUD control: reserved for admin users, includes draft articles
admin_router = APIRouter(
    prefix="/admin/articles",
    tags=["Articles (Admin)"]
)

@admin_router.get("", response_model=List[Article])
async def list_articles_admin(auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    List all active articles including drafts for administrative management.
    Requires 'admin' role.
    """
    return await article_controller.list_articles_handler(include_inactive=True, token=auth_data["token"])

@admin_router.get("/{id}", response_model=Article)
async def get_article_admin(id: UUID, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Get any active article by its UUID (including drafts).
    Requires 'admin' role.
    """
    return await article_controller.get_article_handler(id, include_inactive=True, token=auth_data["token"])

@admin_router.post("", response_model=Article)
async def create_article_admin(article_data: ArticleCreate, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Create a new article.
    Requires 'admin' role.
    """
    return await article_controller.create_article_handler(article_data, token=auth_data["token"])

@admin_router.put("/{id}", response_model=Article)
async def update_article_admin(id: UUID, update_data: ArticleUpdate, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Update an existing article (supports partial updates).
    Requires 'admin' role.
    """
    return await article_controller.update_article_handler(id, update_data, token=auth_data["token"])

@admin_router.delete("/{id}")
async def delete_article_admin(id: UUID, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Soft delete an article.
    Requires 'admin' role.
    """
    return await article_controller.delete_article_handler(id, token=auth_data["token"])
