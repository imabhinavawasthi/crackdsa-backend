from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

# --- Article Base Schema ---
class ArticleBase(BaseModel):
    slug: str
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    category: str = "General"
    difficulty: Optional[str] = None
    read_time_minutes: int = 5
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    resources: Dict[str, Any] = Field(default_factory=dict)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    is_published: bool = False

# --- Article Creation Schema ---
class ArticleCreate(ArticleBase):
    pass

# --- Article Update Schema ---
class ArticleUpdate(BaseModel):
    """
    Schema supporting partial updates for Articles.
    """
    slug: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    read_time_minutes: Optional[int] = None
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    resources: Optional[Dict[str, Any]] = None
    attributes: Optional[Dict[str, Any]] = None
    is_published: Optional[bool] = None

# --- Complete Article Response Schema ---
class Article(ArticleBase):
    id: UUID
    is_active: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
