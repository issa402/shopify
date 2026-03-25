"""
Marketing router — LTV segmentation and personalization.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import random

router = APIRouter()


class CustomerProfile(BaseModel):
    customer_id: str
    total_spent: float
    orders_count: int
    avg_order_value: float
    days_since_first_order: int
    days_since_last_order: int
    product_categories: List[str] = []


class SegmentResponse(BaseModel):
    customer_id: str
    segment: str       # vip | high | medium | low | at_risk | churned
    predicted_ltv: float
    recommended_action: str
    next_best_offer: str


@router.post("/segment")
async def segment_customer(profile: CustomerProfile) -> SegmentResponse:
    """
    Segment a customer by predicted LTV using heuristic scoring.
    Production: replace with Prophet/ML model trained on merchant data.
    """
    # LTV Prediction (simplified scoring model)
    # In production: use trained scikit-learn model or Prophet
    recency_score = max(0, 100 - profile.days_since_last_order * 2)
    frequency_score = min(100, profile.orders_count * 10)
    monetary_score = min(100, profile.total_spent / 10)

    rfm_score = (recency_score * 0.3 + frequency_score * 0.3 + monetary_score * 0.4)
    predicted_ltv = profile.avg_order_value * max(1, profile.orders_count * 1.5)

    if rfm_score >= 70:
        segment = "vip"
        action = "Exclusive early access to new collections"
        offer = "VIP: 15% off next purchase + free shipping"
    elif rfm_score >= 50:
        segment = "high"
        action = "Upsell to premium products"
        offer = "Loyalty offer: 10% off orders over $200"
    elif profile.days_since_last_order > 90:
        segment = "at_risk"
        action = "Win-back campaign"
        offer = "We miss you! 20% off your next order"
    elif rfm_score >= 30:
        segment = "medium"
        action = "Cross-sell complementary products"
        offer = "You might also love these items"
    else:
        segment = "low"
        action = "Nurture with value content"
        offer = "Free shipping on your next order"

    return SegmentResponse(
        customer_id=profile.customer_id,
        segment=segment,
        predicted_ltv=round(predicted_ltv, 2),
        recommended_action=action,
        next_best_offer=offer,
    )


@router.post("/bulk-segment")
async def bulk_segment(profiles: List[CustomerProfile]) -> List[SegmentResponse]:
    """Segment multiple customers at once."""
    results = []
    for profile in profiles:
        result = await segment_customer(profile)
        results.append(result)
    return results
