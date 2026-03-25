"""
Inventory router — forecasting, stockout detection, and PO generation.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from inventory.forecast import InventoryForecaster

router = APIRouter()
forecaster = InventoryForecaster()


class ForecastRequest(BaseModel):
    merchant_id: str
    product_id: str
    sales_history: list[dict]  # [{"date": "2025-01-01", "units_sold": 5}, ...]
    upcoming_campaigns: Optional[list[dict]] = None


class StockoutCheckRequest(BaseModel):
    merchant_id: str
    product_id: str
    current_stock: int
    open_po_quantity: int = 0
    daily_avg_demand: float
    lead_time_days: int = 14


class PurchaseOrderRequest(BaseModel):
    merchant_id: str
    product_id: str
    supplier_name: str
    supplier_sku: str
    quantity_needed: int
    unit_cost: float
    lead_time_days: int = 14


@router.post("/forecast")
async def forecast_demand(request: ForecastRequest):
    """Run Prophet demand forecast for a product."""
    try:
        result = forecaster.forecast_demand(
            product_id=request.product_id,
            sales_history=request.sales_history,
            upcoming_campaigns=request.upcoming_campaigns,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stockout-check")
async def check_stockout(request: StockoutCheckRequest):
    """Check stockout risk and reorder point for a product."""
    result = forecaster.check_stockout_risk(
        product_id=request.product_id,
        current_stock=request.current_stock,
        open_po_quantity=request.open_po_quantity,
        daily_avg_demand=request.daily_avg_demand,
        lead_time_days=request.lead_time_days,
    )
    return result


@router.post("/purchase-order/draft")
async def draft_purchase_order(request: PurchaseOrderRequest):
    """Generate a draft purchase order (requires merchant approval before execution)."""
    po = forecaster.generate_purchase_order(
        product_id=request.product_id,
        supplier_name=request.supplier_name,
        supplier_sku=request.supplier_sku,
        quantity_needed=request.quantity_needed,
        unit_cost=request.unit_cost,
        lead_time_days=request.lead_time_days,
    )
    return {
        "merchant_id": request.merchant_id,
        "purchase_order": po,
        "note": "Awaiting merchant approval via NexusOS Dashboard → Approvals",
    }
