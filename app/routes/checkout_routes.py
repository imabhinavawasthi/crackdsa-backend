from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, List, Optional
import os
import uuid
import razorpay
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel
from app.dependencies import get_current_user, get_supabase_client
from app.schemas.transaction import OrderCreateRequest, OrderCreateResponse, RazorpayWebhookData
from app.schemas.coupon import CouponValidateRequest, CouponValidateResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/checkout",
    tags=["Checkout & Payments"]
)

# Initialize Razorpay Client
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "TEST_KEY")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "TEST_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "TEST_WEBHOOK_SECRET")

rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def get_plan_price(purchase_type: str, target_id: Optional[str]) -> float:
    # Hardcoded prices for now; normally fetched from DB
    if purchase_type == "pro_subscription":
        if target_id == "3_months": return 1.0
        if target_id == "6_months": return 1.0
        if target_id == "12_months": return 1.0
        return 1.0
    elif purchase_type == "course":
        # Assume standard course price
        return 1
    return 0.0

@router.post("/apply-coupon", response_model=CouponValidateResponse)
async def apply_coupon(
    req: CouponValidateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Validate a coupon and return discount details."""
    client = get_supabase_client()
    
    # Fetch coupon
    res = client.table("coupons").select("*").eq("code", req.code).eq("is_active", True).execute()
    if not res.data:
        return CouponValidateResponse(valid=False, message="Invalid or inactive coupon code")
        
    coupon = res.data[0]
    
    # Check max uses
    if coupon["max_uses"] is not None and coupon["used_count"] >= coupon["max_uses"]:
        return CouponValidateResponse(valid=False, message="Coupon usage limit reached")
        
    # Check expiration
    if coupon["valid_until"]:
        valid_until = datetime.fromisoformat(coupon["valid_until"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > valid_until:
            return CouponValidateResponse(valid=False, message="Coupon has expired")
            
    # Check applicability
    applicable = False
    app_list = coupon.get("applicable_to", [])
    if "ALL" in app_list:
        applicable = True
    elif req.purchase_type == "pro_subscription" and "PRO" in app_list:
        applicable = True
    elif req.purchase_type == "course" and req.target_id in app_list:
        applicable = True
        
    if not applicable:
        return CouponValidateResponse(valid=False, message="Coupon is not applicable for this purchase")
        
    return CouponValidateResponse(
        valid=True,
        discount_type=coupon["discount_type"],
        discount_value=float(coupon["discount_value"])
    )


@router.get("/coupons")
async def get_eligible_coupons(
    purchase_type: str,
    target_id: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Fetch all active coupons applicable for a specific purchase."""
    client = get_supabase_client()
    
    # In a real app we'd do a complex query, but since coupons list is small, we'll fetch active ones and filter
    res = client.table("coupons").select("*").eq("is_active", True).execute()
    coupons = res.data or []
    
    eligible = []
    for c in coupons:
        # Check max uses
        if c["max_uses"] is not None and c["used_count"] >= c["max_uses"]:
            continue
            
        # Check expiration
        if c["valid_until"]:
            valid_until = datetime.fromisoformat(c["valid_until"].replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > valid_until:
                continue
                
        app_list = c.get("applicable_to", [])
        is_applicable = False
        if "ALL" in app_list:
            is_applicable = True
        elif purchase_type == "pro_subscription" and "PRO" in app_list:
            is_applicable = True
        elif purchase_type == "course" and target_id in app_list:
            is_applicable = True
            
        if is_applicable:
            eligible.append({
                "code": c["code"],
                "discount_type": c["discount_type"],
                "discount_value": float(c["discount_value"])
            })
            
    return {"coupons": eligible}

@router.post("/create-order", response_model=OrderCreateResponse)
async def create_order(
    req: OrderCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Creates a pending transaction and a Razorpay order."""
    client = get_supabase_client()
    base_price = get_plan_price(req.purchase_type, req.target_id)
    final_price = base_price
    coupon_id = None
    
    if req.coupon_code:
        # Validate coupon again
        val_res = await apply_coupon(CouponValidateRequest(
            code=req.coupon_code,
            purchase_type=req.purchase_type,
            target_id=req.target_id
        ), user)
        
        if val_res.valid:
            # Fetch coupon ID
            c_res = client.table("coupons").select("id").eq("code", req.coupon_code).execute()
            if c_res.data:
                coupon_id = c_res.data[0]["id"]
                
            if val_res.discount_type == "percentage":
                final_price = base_price - (base_price * val_res.discount_value / 100)
            elif val_res.discount_type == "fixed":
                final_price = max(0, base_price - val_res.discount_value)
                
    # Create Razorpay Order
    amount_in_paise = int(final_price * 100)
    
    # In test mode, if keys are invalid, razorpay sdk will throw error
    try:
        rzp_order = rzp_client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": f"receipt_{uuid.uuid4().hex[:8]}",
            "notes": {
                "user_id": user["id"],
                "purchase_type": req.purchase_type,
                "target_id": req.target_id or ""
            }
        })
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {e}")
        # For local development without valid keys, return mock order
        if "TEST_KEY" in RAZORPAY_KEY_ID:
            rzp_order = {"id": f"order_mock_{uuid.uuid4().hex[:8]}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create payment gateway order")
            
    # Create Transaction Record in Supabase
    tx_data = {
        "user_id": user["id"],
        "amount": final_price,
        "currency": "INR",
        "status": "pending",
        "razorpay_order_id": rzp_order["id"],
        "coupon_id": coupon_id,
        "purchase_type": req.purchase_type,
        "target_id": req.target_id,
        "metadata": {"target_name": req.target_name} if req.target_name else {}
    }
    
    db_res = client.table("transactions").insert(tx_data).execute()
    tx_id = db_res.data[0]["id"]
    
    return OrderCreateResponse(
        razorpay_order_id=rzp_order["id"],
        amount=final_price,
        currency="INR",
        transaction_id=tx_id
    )

@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """Handle razorpay successful payment webhook."""
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    
    client = get_supabase_client()
    
    # Verify signature
    try:
        if "TEST_WEBHOOK_SECRET" not in RAZORPAY_WEBHOOK_SECRET:
            rzp_client.utility.verify_webhook_signature(body.decode("utf-8"), signature, RAZORPAY_WEBHOOK_SECRET)
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    payload = await request.json()
    
    if payload.get("event") == "payment.captured":
        payment_entity = payload["payload"]["payment"]["entity"]
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")
        
        # 1. Update Transaction Table
        tx_res = client.table("transactions").select("*").eq("razorpay_order_id", order_id).execute()
        if not tx_res.data:
            return {"status": "ok", "message": "Transaction not found"}
            
        tx = tx_res.data[0]
        if tx["status"] == "success":
            return {"status": "ok", "message": "Already processed"}
            
        # Mark as success
        client.table("transactions").update({
            "status": "success",
            "razorpay_payment_id": payment_id
        }).eq("id", tx["id"]).execute()
        
        # Increment coupon uses
        if tx["coupon_id"]:
            # Basic increment, in a real app use an RPC for atomicity
            c_res = client.table("coupons").select("used_count").eq("id", tx["coupon_id"]).execute()
            if c_res.data:
                client.table("coupons").update({
                    "used_count": c_res.data[0]["used_count"] + 1
                }).eq("id", tx["coupon_id"]).execute()
        
        # 2. Grant Access in Users Table
        user_id = tx["user_id"]
        user_res = client.table("users").select("*").eq("id", user_id).execute()
        if user_res.data:
            user_row = user_res.data[0]
            now = datetime.now(timezone.utc)
            now_iso = now.isoformat()
            
            if tx["purchase_type"] == "pro_subscription":
                plan_id = tx["target_id"]
                days = -1
                if plan_id == "monthly": days = 30
                elif plan_id == "six-months": days = 180
                
                pro_sub = user_row.get("pro_subscription") or {}
                
                all_purchases = pro_sub.get("all_purchases", [])
                
                purchase_entry = {
                    "duration_in_days": str(days),
                    "purchase_date_epoch": int(now.timestamp()),
                    "transaction_id": str(tx["id"])
                }
                all_purchases.append(purchase_entry)
                
                current_expiry_epoch = pro_sub.get("subscription_active_till_epoch", 0)
                
                if current_expiry_epoch == -1 or days == -1:
                    new_expiry_epoch = -1
                else:
                    if current_expiry_epoch > int(now.timestamp()):
                        new_expiry_epoch = current_expiry_epoch + (days * 86400)
                    else:
                        new_expiry_epoch = int(now.timestamp()) + (days * 86400)
                        
                pro_sub["all_purchases"] = all_purchases
                pro_sub["subscription_active_till_epoch"] = new_expiry_epoch
                
                client.table("users").update({"pro_subscription": pro_sub}).eq("id", user_id).execute()
                
            elif tx["purchase_type"] == "course":
                purchased_courses = user_row.get("purchased_courses") or {}
                courses_arr = purchased_courses.get("courses", [])
                
                course_id = tx["target_id"]
                metadata = tx.get("metadata") or {}
                course_name = metadata.get("target_name", course_id)
                
                # Check if already purchased
                already_purchased = any(c.get("course_id") == course_id for c in courses_arr)
                
                if not already_purchased:
                    courses_arr.append({
                        "course_id": course_id,
                        "purchase_date_epoch": int(now.timestamp()),
                        "valid_till_epoch": -1,
                        "course_name": course_name,
                        "transaction_id": str(tx["id"])
                    })
                    
                    purchased_courses["courses"] = courses_arr
                    client.table("users").update({"purchased_courses": purchased_courses}).eq("id", user_id).execute()
                
    return {"status": "ok"}

@router.get("/transactions")
async def get_my_transactions(user: Dict[str, Any] = Depends(get_current_user)):
    """Fetch the authenticated user's transactions."""
    client = get_supabase_client()
    res = client.table("transactions").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute()
    
    transactions = res.data or []
    now = datetime.now(timezone.utc)
    
    for tx in transactions:
        if tx["status"] == "pending":
            try:
                tx_created = datetime.fromisoformat(tx["created_at"].replace("Z", "+00:00"))
                if (now - tx_created).total_seconds() > 86400: # 1 day
                    tx["status"] = "failed"
                    try:
                        client.table("transactions").update({
                            "status": "failed",
                            "failure_reason": "timeout"
                        }).eq("id", tx["id"]).execute()
                        tx["failure_reason"] = "timeout"
                    except Exception:
                        # Fallback if failure_reason column doesn't exist
                        client.table("transactions").update({
                            "status": "failed"
                        }).eq("id", tx["id"]).execute()
            except Exception as e:
                logger.error(f"Failed to check timeout for tx {tx['id']}: {e}")
                
    return {"items": transactions}


