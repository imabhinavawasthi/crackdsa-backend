from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

# --- Practice Problem Base Schema ---
class PracticeProblemBase(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    difficulty: str
    platform: str = "Internal"
    problem_url: Optional[str] = None
    solutions: Dict[str, Any] = Field(default_factory=dict)
    resources: Dict[str, Any] = Field(default_factory=dict)
    attributes: Dict[str, Any] = Field(default_factory=dict)

# --- Practice Problem Creation Schema ---
class PracticeProblemCreate(PracticeProblemBase):
    pass

# --- Practice Problem Update Schema ---
class PracticeProblemUpdate(BaseModel):
    """
    Schema supporting partial updates for Practice Problems.
    """
    slug: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    platform: Optional[str] = None
    problem_url: Optional[str] = None
    solutions: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    attributes: Optional[Dict[str, Any]] = None

# --- Complete Practice Problem Response Schema ---
class PracticeProblem(PracticeProblemBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Basic Practice Problem Response Schema (for table listings) ---
class PracticeProblemBasic(BaseModel):
    id: UUID
    slug: str
    title: str
    difficulty: str
    platform: str
    problem_url: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
