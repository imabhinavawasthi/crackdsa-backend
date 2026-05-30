from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

# ============ REQUEST SCHEMAS ============

class InstructorCreateSchema(BaseModel):
    """Schema for creating a new instructor (admin only)"""
    name: str = Field(..., min_length=1, max_length=255, description="Instructor full name")
    role: str = Field(..., min_length=1, max_length=255, description="Role/Title")
    sub_title: Optional[str] = Field(None, max_length=255, description="Subtitle or tagline")
    bio: Optional[str] = Field(None, description="Extended biography")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata (UI colors, social links, etc.)")

    class Config:
        example = {
            "name": "Abhinav Awasthi",
            "role": "Founder, CrackDSA",
            "sub_title": "Ex-Google SDE",
            "bio": "10+ years of experience in software engineering...",
            "profile_image_url": "https://example.com/avatar.jpg",
            "metadata": {
                "color": "from-brand-500 to-blue-light-400",
                "twitter": "@username",
                "linkedin": "username"
            }
        }


class InstructorUpdateSchema(BaseModel):
    """Schema for updating an instructor (admin only)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, min_length=1, max_length=255)
    sub_title: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    class Config:
        example = {
            "bio": "Updated biography...",
            "sub_title": "Ex-Google SDE",
            "metadata": {"color": "from-purple-500 to-pink-400"}
        }


# ============ RESPONSE SCHEMAS ============

class InstructorResponseSchema(BaseModel):
    """Schema for instructor response (public & admin)"""
    id: UUID
    name: str
    role: str
    sub_title: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    metadata: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        example = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Abhinav Awasthi",
            "role": "Founder, CrackDSA",
            "sub_title": "Ex-Google SDE",
            "bio": "10+ years of experience...",
            "profile_image_url": "https://example.com/avatar.jpg",
            "metadata": {
                "color": "from-brand-500 to-blue-light-400",
                "twitter": "@username"
            },
            "is_active": True,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }


class InstructorListResponseSchema(BaseModel):
    """Schema for list of instructors"""
    items: list[InstructorResponseSchema]
    total: int
    limit: int
    offset: int

    class Config:
        example = {
            "items": [],
            "total": 10,
            "limit": 20,
            "offset": 0
        }
