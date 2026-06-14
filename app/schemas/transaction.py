from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID

class TransactionBase(BaseModel):
    amount: float
    currency: str = "INR"
    status: Literal["pending", "success", "failed"] = "pending"
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    coupon_id: Optional[UUID] = None
    purchase_type: Literal["pro_subscription", "course"]
    target_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    status: Optional[Literal["pending", "success", "failed"]] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None

class TransactionResponse(TransactionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderCreateRequest(BaseModel):
    purchase_type: Literal["pro_subscription", "course"]
    target_id: Optional[str] = None
    coupon_code: Optional[str] = None

class OrderCreateResponse(BaseModel):
    razorpay_order_id: str
    amount: float
    currency: str
    transaction_id: UUID
    
class RazorpayWebhookData(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


