"""
Agents router — exposes endpoints to trigger agent swarms.
"""
import uuid
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from agents.crew import create_swarm, resolve_support_ticket, handle_supply_disruption

router = APIRouter()


class SupportTicketRequest(BaseModel):
    merchant_id: str
    customer_name: str
    order_id: str
    issue: str
    requested_resolution: str


class SupplyDisruptionRequest(BaseModel):
    merchant_id: str
    product_name: str
    supplier: str
    delay_days: int
    current_stock: int
    daily_sales: float


@router.post("/support/resolve")
async def resolve_ticket(request: SupportTicketRequest):
    """Trigger the Support Agent Swarm to resolve a customer ticket."""
    try:
        crew = create_swarm(request.merchant_id)
        result = resolve_support_ticket(crew, request.dict())
        return {
            "status": "resolved",
            "merchant_id": request.merchant_id,
            "order_id": request.order_id,
            "result": result,
            "resolved_by": "SupportAgent + FinanceAgent (CrewAI Swarm)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logistics/disruption")
async def handle_disruption(request: SupplyDisruptionRequest):
    """Trigger the Logistics Agent Swarm to handle a supply chain disruption."""
    try:
        crew = create_swarm(request.merchant_id)
        result = handle_supply_disruption(crew, request.dict())
        return {
            "status": "handled",
            "merchant_id": request.merchant_id,
            "product": request.product_name,
            "result": result,
            "handled_by": "LogisticsAgent + FinanceAgent (CrewAI Swarm)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{merchant_id}")
async def agent_status(merchant_id: str):
    """Return a summary of agent activity for this merchant."""
    # TODO: query ai_decisions table for recent activity
    return {
        "merchant_id": merchant_id,
        "agents": [
            {"name": "SupportAgent", "status": "idle", "tasks_today": 0},
            {"name": "LogisticsAgent", "status": "idle", "tasks_today": 0},
            {"name": "FinanceAgent", "status": "idle", "tasks_today": 0},
        ],
        "pending_approvals": 0,
        "total_cost_today_usd": 0.00,
    }
