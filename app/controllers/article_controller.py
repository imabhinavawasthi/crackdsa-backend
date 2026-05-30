from typing import List
from fastapi import HTTPException
from app.schemas.article import ArticleCreate, ArticleUpdate
from app.services import article_service
from uuid import UUID

async def list_articles_handler(include_inactive: bool = False, token: str = None) -> List[dict]:
    """
    Controller handler to list articles.
    """
    try:
        return article_service.get_articles(include_inactive=include_inactive, token=token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch articles: {str(e)}")

async def get_article_handler(article_id: UUID, include_inactive: bool = False, token: str = None) -> dict:
    """
    Controller handler to retrieve a single article by UUID.
    """
    try:
        article = article_service.get_article_by_id(article_id, include_inactive=include_inactive, token=token)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return article
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_article_by_slug_handler(slug: str, include_inactive: bool = False, token: str = None) -> dict:
    """
    Controller handler to retrieve a single article by slug.
    """
    try:
        article = article_service.get_article_by_slug(slug, include_inactive=include_inactive, token=token)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return article
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_article_handler(article_data: ArticleCreate, token: str = None) -> dict:
    """
    Controller handler to create a new article.
    """
    try:
        return article_service.create_article(article_data, token=token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def update_article_handler(article_id: UUID, update_data: ArticleUpdate, token: str = None) -> dict:
    """
    Controller handler to update an existing article.
    """
    try:
        return article_service.update_article(article_id, update_data, token=token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def delete_article_handler(article_id: UUID, token: str = None) -> dict:
    """
    Controller handler to soft-delete an existing article.
    """
    try:
        article_service.soft_delete_article(article_id, token=token)
        return {"message": "Article deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
