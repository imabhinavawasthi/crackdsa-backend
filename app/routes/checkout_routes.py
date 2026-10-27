from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, List, Optional
import os
import uuid
import razorpay
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel
from app.dependencies import get_current_user, get_current_user_optional, get_supabase_client
from app.schemas.transaction import (
    OrderCreateRequest,
    OrderCreateResponse,
    PaymentVerifyRequest,
    RazorpayWebhookData,
)
from app.schemas.coupon import CouponValidateRequest, CouponValidateResponse
from app.pro_pricing import PRO_PRICING_CONFIG, get_pro_price, get_pro_duration_days
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/checkout",
    tags=["Checkout & Payments"]
)

# Helper to get dynamically configured Razorpay client
def get_razorpay_client():
    key_id = os.environ.get("RAZORPAY_KEY_ID", "TEST_KEY")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "TEST_SECRET")
    client = razorpay.Client(auth=(key_id, key_secret))
    return client, key_id, key_secret


def get_plan_price(purchase_type: str, target_id: Optional[str]) -> float:
    """Resolve price for subscription plans or individual courses."""
    if purchase_type == "pro_subscription":
        return get_pro_price(target_id)
    elif purchase_type == "course":
        if target_id:
            try:
                client = get_supabase_client()
                from uuid import UUID
                try:
                    UUID(target_id)
                    c_res = client.table("courses").select("price").eq("id", target_id).execute()
                except ValueError:
                    c_res = client.table("courses").select("price").eq("slug", target_id).execute()
                if c_res.data and c_res.data[0].get("price") is not None:
                    return float(c_res.data[0]["price"])
            except Exception as e:
                logger.error(f"Error fetching course price: {e}")
        return 2999.0
    return 0.0

@router.get("/pro-pricing")
async def get_pro_pricing():
    """Retrieve active CrackDSA Pro pricing tiers and durations."""
    return {
        "plans": {k: v.model_dump() for k, v in PRO_PRICING_CONFIG.items()}
    }


@router.post("/apply-coupon", response_model=CouponValidateResponse)
async def apply_coupon(
    req: CouponValidateRequest,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
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
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
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
    rzp_client, current_key_id, _ = get_razorpay_client()
    
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
        if current_key_id == "TEST_KEY":
            logger.warning("Using mock order simulation due to TEST_KEY placeholder.")
            rzp_order = {"id": f"order_mock_{uuid.uuid4().hex[:8]}"}
        else:
            raise HTTPException(status_code=500, detail=f"Payment gateway order creation failed: {str(e)}")
            
    # Ensure user exists in public.users to avoid foreign key violation
    u_check = client.table("users").select("id").eq("id", user["id"]).execute()
    if not u_check.data:
        logger.warning(f"User {user['id']} missing from public.users during checkout. Auto-creating entry.")
        client.table("users").insert({
            "id": user["id"],
            "user_email": user.get("email"),
            "college": None,
            "graduation_year": None,
            "branch": None,
            "codeforces_id": None,
            "bookmarked_problems": [],
            "pending_problems": [],
            "trying_problems": [],
            "solved_problems": [],
            "revise_problems": [],
            "social_links": {},
            "metadata": {
                "full_name": user.get("full_name") or "",
                "avatar_url": user.get("avatar_url") or "",
                "onboarding_completed": True
            },
            "pro_subscription": {},
            "purchased_courses": {}
        }).execute()

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
        transaction_id=tx_id,
        razorpay_key_id=current_key_id
    )


def fulfill_purchase(client: Any, tx: Dict[str, Any], payment_id: Optional[str] = None):
    """Safely and idempotently fulfill user access for subscription or course."""
    # 1. Update transaction status
    update_data: Dict[str, Any] = {"status": "success"}
    if payment_id:
        update_data["razorpay_payment_id"] = payment_id
    client.table("transactions").update(update_data).eq("id", tx["id"]).execute()

    # 2. Increment coupon uses if applicable
    if tx.get("coupon_id"):
        c_res = client.table("coupons").select("used_count").eq("id", tx["coupon_id"]).execute()
        if c_res.data:
            client.table("coupons").update({
                "used_count": c_res.data[0]["used_count"] + 1
            }).eq("id", tx["coupon_id"]).execute()

    # 3. Grant access in users table
    user_id = tx["user_id"]
    user_res = client.table("users").select("*").eq("id", user_id).execute()
    if not user_res.data:
        return

    user_row = user_res.data[0]
    now = datetime.now(timezone.utc)

    if tx["purchase_type"] == "pro_subscription":
        plan_id = tx.get("target_id")
        days = get_pro_duration_days(plan_id)

        pro_sub = user_row.get("pro_subscription") or {}
        all_purchases = pro_sub.get("all_purchases", [])

        # Avoid duplicate purchase entries for this transaction
        if not any(str(p.get("transaction_id")) == str(tx["id"]) for p in all_purchases):
            all_purchases.append({
                "duration_in_days": days,
                "purchase_date_epoch": int(now.timestamp()),
                "transaction_id": str(tx["id"])
            })

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
        if not isinstance(purchased_courses, dict):
            purchased_courses = {"courses": []}
        courses_arr = purchased_courses.get("courses", [])
        if not isinstance(courses_arr, list):
            courses_arr = []

        target = tx.get("target_id") or ""
        metadata = tx.get("metadata") or {}

        # Look up course row to capture canonical UUID, slug, and title
        c_res = client.table("courses").select("id, slug, title").or_(f"id.eq.{target},slug.eq.{target}").execute()
        if not c_res.data and target == "data-structures-algorithms-mastery-program":
            c_res = client.table("courses").select("id, slug, title").eq("slug", "dsa").execute()

        c_id = str(c_res.data[0]["id"]) if c_res.data else str(target)
        c_slug = str(c_res.data[0]["slug"]) if c_res.data else str(target)
        c_title = c_res.data[0]["title"] if c_res.data else (metadata.get("target_name") or target)

        already_purchased = any(
            str(c.get("course_id") or "") in (c_id, c_slug) or
            str(c.get("course_slug") or "") in (c_id, c_slug)
            for c in courses_arr
        )
        if not already_purchased:
            courses_arr.append({
                "course_id": c_id,
                "course_slug": c_slug,
                "course_name": c_title,
                "purchase_date_epoch": int(now.timestamp()),
                "valid_till_epoch": -1,
                "transaction_id": str(tx["id"])
            })
            purchased_courses["courses"] = courses_arr
            client.table("users").update({"purchased_courses": purchased_courses}).eq("id", user_id).execute()

    # 4. Invalidate relevant caches immediately
    try:
        from app.utils.cache import cache_manager
        cache_manager.invalidate_namespace("live_classes")
        cache_manager.invalidate_namespace("courses")
    except Exception as e:
        logger.warning(f"Cache invalidation error after purchase fulfillment: {e}")


@router.post("/verify")
async def verify_payment(
    req: PaymentVerifyRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Verify payment signature from client checkout modal and fulfill access immediately."""
    client = get_supabase_client()

    # Look up transaction
    tx_res = client.table("transactions").select("*").eq("id", req.transaction_id).execute()
    if not tx_res.data:
        # Fallback to razorpay_order_id
        if req.razorpay_order_id:
            tx_res = client.table("transactions").select("*").eq("razorpay_order_id", req.razorpay_order_id).execute()

    if not tx_res.data:
        raise HTTPException(status_code=404, detail="Transaction not found")

    tx = tx_res.data[0]

    # If already fulfilled
    if tx["status"] == "success":
        return {"status": "ok", "message": "Transaction already verified and active"}

    # Signature verification (skip if test mock order)
    if not str(tx.get("razorpay_order_id", "")).startswith("order_mock_"):
        if req.razorpay_order_id and req.razorpay_payment_id and req.razorpay_signature:
            rzp_client, _, _ = get_razorpay_client()
            try:
                rzp_client.utility.verify_payment_signature({
                    "razorpay_order_id": req.razorpay_order_id,
                    "razorpay_payment_id": req.razorpay_payment_id,
                    "razorpay_signature": req.razorpay_signature,
                })
            except Exception as e:
                logger.error(f"Payment signature verification failed: {e}")
                raise HTTPException(status_code=400, detail="Invalid payment signature")

    fulfill_purchase(client, tx, req.razorpay_payment_id)
    return {"status": "success", "message": "Payment verified and access activated"}


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """Handle razorpay successful payment webhook."""
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    
    client = get_supabase_client()
    rzp_client, _, _ = get_razorpay_client()
    webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "TEST_WEBHOOK_SECRET")
    
    # Verify signature
    try:
        if "TEST_WEBHOOK_SECRET" not in webhook_secret:
            rzp_client.utility.verify_webhook_signature(body.decode("utf-8"), signature, webhook_secret)
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    payload = await request.json()
    
    if payload.get("event") in ["payment.captured", "order.paid"]:
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")
        
        if not order_id and "order" in payload.get("payload", {}):
            order_id = payload["payload"]["order"]["entity"].get("id")
        
        tx_res = client.table("transactions").select("*").eq("razorpay_order_id", order_id).execute()
        if not tx_res.data:
            return {"status": "ok", "message": "Transaction not found"}
            
        tx = tx_res.data[0]
        if tx["status"] == "success":
            return {"status": "ok", "message": "Already processed"}
            
        fulfill_purchase(client, tx, payment_id)
                
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


