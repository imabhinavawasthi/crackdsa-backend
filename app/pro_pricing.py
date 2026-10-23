"""
Centralized Pro Pricing Configuration for CrackDSA Pro (Backend).
Single source of truth for subscription plans, pricing, and access durations.
"""

from typing import Dict, Optional
from pydantic import BaseModel


class ProPlanConfig(BaseModel):
    id: str
    name: str
    subtitle: str
    price: float
    original_price: float
    billing_period: str
    discount_percent: int
    duration_days: int  # 30, 730, or -1 for lifetime
    duration_months: int  # 1, 24, or -1 for lifetime
    badge: Optional[str] = None


PRO_PRICING_CONFIG: Dict[str, ProPlanConfig] = {
    "monthly": ProPlanConfig(
        id="monthly",
        name="Monthly Pro",
        subtitle="Flexible monthly access",
        price=799.0,
        original_price=1599.0,
        billing_period="per month",
        discount_percent=50,
        duration_days=30,
        duration_months=1,
        badge="FLEXIBLE",
    ),
    "yearly": ProPlanConfig(
        id="yearly",
        name="2-Year Pro Pass",
        subtitle="Complete interview preparation",
        price=5999.0,
        original_price=16999.0,
        billing_period="2 full years",
        discount_percent=62,
        duration_days=730,
        duration_months=24,
        badge="MOST POPULAR",
    ),
    "lifetime": ProPlanConfig(
        id="lifetime",
        name="Lifetime Member Pass",
        subtitle="Pay once, learn forever",
        price=9999.0,
        original_price=20000.0,
        billing_period="one-time payment",
        discount_percent=50,
        duration_days=-1,
        duration_months=-1,
        badge="LONG-TERM",
    ),
}

# Legacy aliases for backward compatibility if any old checkout order used legacy slugs
LEGACY_ALIASES: Dict[str, str] = {
    "3_months": "monthly",
    "12_months": "yearly",
    "2_year": "yearly",
}


def get_pro_plan(plan_id: Optional[str]) -> ProPlanConfig:
    """Retrieve plan configuration with fallback to yearly (most popular)."""
    if not plan_id:
        return PRO_PRICING_CONFIG["yearly"]
    resolved_id = LEGACY_ALIASES.get(plan_id, plan_id)
    return PRO_PRICING_CONFIG.get(resolved_id, PRO_PRICING_CONFIG["yearly"])


def get_pro_price(plan_id: Optional[str]) -> float:
    """Retrieve price for a specific Pro plan."""
    return get_pro_plan(plan_id).price


def get_pro_duration_days(plan_id: Optional[str]) -> int:
    """Retrieve duration in days for a specific Pro plan (-1 for lifetime)."""
    return get_pro_plan(plan_id).duration_days
