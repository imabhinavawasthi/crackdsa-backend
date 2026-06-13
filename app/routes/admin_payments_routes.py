from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Dict, Any, Optional
from app.dependencies import verify_admin_token, get_supabase_client
from app.schemas.coupon import CouponCreate, CouponUpdate, CouponResponse
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/payments",
    tags=["Payments & Coupons (Admin)"]
)

# --- Coupons ---

@router.get("/coupons", response_model=List[CouponResponse])
def list_coupons_admin(admin_user = Depends(verify_admin_token)):
    """List all coupons."""
    client = get_supabase_client()
    try:
        res = client.table("coupons").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Error fetching coupons: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch coupons")

@router.post("/coupons", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon_admin(
    data: CouponCreate,
    admin_user = Depends(verify_admin_token),
):
    """Create a new coupon."""
    client = get_supabase_client()
    try:
        payload = data.model_dump()
        if payload["valid_until"]:
            payload["valid_until"] = payload["valid_until"].isoformat()
            
        res = client.table("coupons").insert(payload).execute()
        if not res.data:
            raise Exception("No data returned")
        return res.data[0]
    except Exception as e:
        logger.error(f"Error creating coupon: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to create coupon: {str(e)}")

@router.put("/coupons/{coupon_id}", response_model=CouponResponse)
def update_coupon_admin(
    coupon_id: str,
    data: CouponUpdate,
    admin_user = Depends(verify_admin_token),
):
    """Update an existing coupon."""
    client = get_supabase_client()
    try:
        payload = data.model_dump(exclude_unset=True)
        if "valid_until" in payload and payload["valid_until"]:
            payload["valid_until"] = payload["valid_until"].isoformat()
            
        res = client.table("coupons").update(payload).eq("id", coupon_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Coupon not found")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating coupon: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to update coupon: {str(e)}")

@router.delete("/coupons/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coupon_admin(
    coupon_id: str,
    admin_user = Depends(verify_admin_token),
):
    """Delete a coupon."""
    client = get_supabase_client()
    try:
        res = client.table("coupons").delete().eq("id", coupon_id).execute()
        return None
    except Exception as e:
        logger.error(f"Error deleting coupon: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to delete coupon: {str(e)}")

# --- Transactions ---

@router.get("/transactions")
def list_transactions_admin(
    status: Optional[str] = None,
    purchase_type: Optional[str] = None,
    admin_user = Depends(verify_admin_token)
):
    """List transactions with optional filters. In a real app we'd paginate."""
    client = get_supabase_client()
    try:
        query = client.table("transactions").select("*, users:user_id(email, full_name)").order("created_at", desc=True)
        if status:
            query = query.eq("status", status)
        if purchase_type:
            query = query.eq("purchase_type", purchase_type)
            
        res = query.execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")
