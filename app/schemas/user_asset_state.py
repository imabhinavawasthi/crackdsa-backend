from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class AssetTypeEnum(str, Enum):
    VIDEO = "video"
    PROBLEM = "problem"
    ARTICLE = "article"

class AssetStatusEnum(str, Enum):
    PENDING = "pending"
    DONE = "done"
    REVISION = "revision"

class NoteSchema(BaseModel):
    id: str
    text: str
    createdAt: str  # Matches frontend NotesTab display format

class UserAssetStateResponseSchema(BaseModel):
    id: str                     # UUID string
    user_id: str                # UUID string
    asset_id: str
    asset_type: AssetTypeEnum
    status: AssetStatusEnum
    is_bookmarked: bool
    bookmarked_at: Optional[datetime] = None
    notes: List[NoteSchema] = []
    metadata: dict = {}
    last_interacted_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserAssetStateUpdateSchema(BaseModel):
    status: Optional[AssetStatusEnum] = None
    is_bookmarked: Optional[bool] = None
    notes: Optional[List[NoteSchema]] = None
    metadata: Optional[dict] = None
