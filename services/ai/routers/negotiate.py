"""
Negotiate router — A2A commerce negotiation via Python AI service.
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from agents.negotiation import NegotiationEngine, ProductQuery

router = APIRouter()
engine = NegotiationEngine()


@router.post("/offer")
async def get_offer(query: ProductQuery, x_agent_type: Optional[str] = Header(None)):
    """Process an A2A ProductQuery and return a structured Offer."""
    try:
        # Merchant ID would come from JWT / session in production
        merchant_id = "demo-merchant"
        offer = await engine.process_query(query, merchant_id)
        return offer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contract")
async def generate_contract(offer_id: str, query: ProductQuery):
    """Convert an accepted Offer into a Contract."""
    # In production: retrieve offer from Redis/DB by offer_id
    offer = await engine.process_query(query, "demo-merchant")
    contract = engine.generate_contract(offer, query)
    return contract
