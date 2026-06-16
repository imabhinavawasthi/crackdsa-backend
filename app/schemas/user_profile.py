from pydantic import BaseModel
from typing import Optional, List, Dict, Union
from datetime import datetime

class PurchasedCourse(BaseModel):
    start_time: str
    end_time: Union[str, int]  # -1 for lifetime, or ISO datetime string
    transaction_id: str

class ProPurchaseHistory(BaseModel):
    plan: str
    start_time: str
    added_duration_months: int  # -1 for lifetime
    transaction_id: str

class ProSubscription(BaseModel):
    is_active: bool
    plan: str
    start_time: str
    end_time: Union[str, int]  # -1 for lifetime, or ISO datetime string
    transaction_id: str
    history: List[ProPurchaseHistory] = []
