from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID

class CouponBase(BaseModel):
    code: str = Field(..., description="The unique coupon code e.g. CRACKDSA50")
    discount_type: Literal["percentage", "fixed"]
    discount_value: float = Field(..., description="Percentage or fixed amount off")
    max_uses: Optional[int] = None
    valid_until: Optional[datetime] = None
    applicable_to: List[str] = Field(default_factory=list, description="List of course IDs or 'PRO'")
    is_active: bool = True

class CouponCreate(CouponBase):
    pass

class CouponUpdate(BaseModel):
    is_active: Optional[bool] = None
    max_uses: Optional[int] = None
    valid_until: Optional[datetime] = None

class CouponResponse(CouponBase):
    id: UUID
    used_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CouponValidateRequest(BaseModel):
    code: str
    purchase_type: Literal["pro_subscription", "course"]
    target_id: Optional[str] = None

class CouponValidateResponse(BaseModel):
    valid: bool
    discount_type: Optional[Literal["percentage", "fixed"]] = None
    discount_value: Optional[float] = None
    message: Optional[str] = None
