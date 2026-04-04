from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# --- Nested JSON Structure ---

class ProblemReference(BaseModel):
    problem_id: str

class Step(BaseModel):
    id: str
    title: str
    pattern_id: str
    problems: List[ProblemReference]

class Topic(BaseModel):
    id: str
    title: str
    steps: List[Step]

class SheetJSON(BaseModel):
    topics: List[Topic]

# --- Main Schema ---

class DSASheetBase(BaseModel):
    title: str
    description: Optional[str] = None
    tags: List[str] = []
    level: Literal['beginner', 'intermediate', 'advanced']
    estimated_hours: Optional[int] = None
    is_public: bool = True
    sheet_json: SheetJSON

class DSASheetCreate(DSASheetBase):
    id: str  # Required for creation as per "crackdsa_75" pattern

class DSASheetUpdate(BaseModel):
    """
    Schema for updating an existing DSA sheet.
    All fields are optional to support partial updates.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    level: Optional[Literal['beginner', 'intermediate', 'advanced']] = None
    estimated_hours: Optional[int] = None
    is_public: Optional[bool] = None
    sheet_json: Optional[SheetJSON] = None

class DSASheet(DSASheetBase):
    id: str
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
