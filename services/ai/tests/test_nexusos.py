"""
NexusOS Python AI Service — Unit Tests
Run: cd services/ai && python -m pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


# ─── Hybrid AI Router Tests ───────────────────────────────────────────────────

class TestHybridRouter:
    def test_cheap_tasks_route_to_ollama(self):
        from agents.router import HybridAIRouter, TaskComplexity, TASK_ROUTING_TABLE
        assert TASK_ROUTING_TABLE["classify_email"] == TaskComplexity.CHEAP
        assert TASK_ROUTING_TABLE["tag_ticket"] == TaskComplexity.CHEAP
        assert TASK_ROUTING_TABLE["sentiment_analysis"] == TaskComplexity.CHEAP

    def test_normal_tasks_route_to_claude(self):
        from agents.router import TaskComplexity, TASK_ROUTING_TABLE
        assert TASK_ROUTING_TABLE["draft_customer_reply"] == TaskComplexity.NORMAL
        assert TASK_ROUTING_TABLE["marketing_copy"] == TaskComplexity.NORMAL

    def test_complex_tasks_route_to_openai(self):
        from agents.router import TaskComplexity, TASK_ROUTING_TABLE
        assert TASK_ROUTING_TABLE["financial_analysis"] == TaskComplexity.COMPLEX
        assert TASK_ROUTING_TABLE["risk_assessment"] == TaskComplexity.COMPLEX

    def test_unknown_task_defaults_to_normal(self):
        from agents.router import HybridAIRouter, TASK_ROUTING_TABLE, TaskComplexity
        assert TASK_ROUTING_TABLE.get("unknown_task_xyz", TaskComplexity.NORMAL) == TaskComplexity.NORMAL

    def test_cost_estimate_cheap_is_zero(self):
        from agents.router import HybridAIRouter
        router = HybridAIRouter()
        cost = router.estimate_cost("classify_email", 1000, 200)
        assert cost == 0.0, f"Expected 0 cost for ollama task, got {cost}"

    def test_cost_estimate_complex_is_higher(self):
        from agents.router import HybridAIRouter
        router = HybridAIRouter()
        cheap_cost = router.estimate_cost("classify_email", 1000, 200)
        complex_cost = router.estimate_cost("financial_analysis", 1000, 200)
        assert complex_cost > cheap_cost


# ─── Inventory Forecaster Tests ────────────────────────────────────────────────

class TestInventoryForecaster:
    def test_reorder_point_calculation(self):
        from inventory.forecast import InventoryForecaster
        f = InventoryForecaster()
        rop = f.calculate_reorder_point(daily_avg_demand=10.0, lead_time_days=14, safety_stock_days=7)
        # ROP = (10 * 14) + (10 * 7) = 140 + 70 = 210
        assert rop == 210, f"Expected 210, got {rop}"

    def test_stockout_critical_urgency(self):
        from inventory.forecast import InventoryForecaster
        f = InventoryForecaster()
        result = f.check_stockout_risk(
            product_id="test-prod",
            current_stock=5,
            open_po_quantity=0,
            daily_avg_demand=2.0,
            lead_time_days=14,
        )
        assert result["urgency"] == "CRITICAL"
        assert result["days_of_stock_remaining"] == 2.5
        assert result["needs_reorder"] is True

    def test_stockout_low_urgency(self):
        from inventory.forecast import InventoryForecaster
        f = InventoryForecaster()
        result = f.check_stockout_risk(
            product_id="test-prod",
            current_stock=1000,
            open_po_quantity=500,
            daily_avg_demand=5.0,
            lead_time_days=14,
        )
        assert result["urgency"] == "LOW"

    def test_simple_forecast_fallback(self):
        from inventory.forecast import InventoryForecaster
        f = InventoryForecaster()
        history = [{"date": f"2025-01-0{i+1}", "units_sold": 5} for i in range(5)]
        result = f._simple_forecast("prod-abc", history)
        assert result["daily_average_units"] == 5.0
        assert "method" in result

    def test_draft_po_structure(self):
        from inventory.forecast import InventoryForecaster
        f = InventoryForecaster()
        po = f.generate_purchase_order(
            product_id="prod-001",
            supplier_name="TestSupplier",
            supplier_sku="SKU-001",
            quantity_needed=100,
            unit_cost=10.0,
            lead_time_days=14,
        )
        assert po["total_cost_usd"] == 1000.0
        assert po["status"] == "pending_merchant_approval"
        assert po["generated_by"] == "LogisticsAgent"


# ─── A2A Negotiation Engine Tests ────────────────────────────────────────────

class TestNegotiationEngine:
    def test_no_discount_for_retail(self):
        from agents.negotiation import NegotiationEngine, QueryConstraints
        engine = NegotiationEngine()
        query_mock = type('Q', (), {'constraints': QueryConstraints(b2b=False), 'quantity': 1})()
        discount = engine._calculate_discount(query_mock)
        assert discount == 0.0

    def test_b2b_10_unit_gets_10_percent(self):
        from agents.negotiation import NegotiationEngine, QueryConstraints
        engine = NegotiationEngine()
        query_mock = type('Q', (), {'constraints': QueryConstraints(b2b=True), 'quantity': 10})()
        discount = engine._calculate_discount(query_mock)
        assert discount == 10.0

    def test_b2b_50_unit_gets_20_percent(self):
        from agents.negotiation import NegotiationEngine, QueryConstraints
        engine = NegotiationEngine()
        query_mock = type('Q', (), {'constraints': QueryConstraints(b2b=True), 'quantity': 50})()
        discount = engine._calculate_discount(query_mock)
        assert discount == 20.0

    def test_discount_never_exceeds_max(self):
        from agents.negotiation import NegotiationEngine, QueryConstraints
        engine = NegotiationEngine()
        engine.max_discount_pct = 15.0  # Override for test
        query_mock = type('Q', (), {'constraints': QueryConstraints(b2b=True), 'quantity': 1000})()
        discount = engine._calculate_discount(query_mock)
        assert discount <= 15.0


# ─── Marketing Segmentation Tests ────────────────────────────────────────────

class TestMarketing:
    @pytest.mark.asyncio
    async def test_vip_segment(self):
        from routers.marketing import segment_customer, CustomerProfile
        profile = CustomerProfile(
            customer_id="cust-001",
            total_spent=5000.0,
            orders_count=15,
            avg_order_value=333.0,
            days_since_first_order=365,
            days_since_last_order=5,
        )
        result = await segment_customer(profile)
        assert result.segment == "vip"
        assert result.predicted_ltv > 0

    @pytest.mark.asyncio
    async def test_at_risk_segment(self):
        from routers.marketing import segment_customer, CustomerProfile
        profile = CustomerProfile(
            customer_id="cust-002",
            total_spent=200.0,
            orders_count=2,
            avg_order_value=100.0,
            days_since_first_order=200,
            days_since_last_order=120,  # Last order 120 days ago
        )
        result = await segment_customer(profile)
        assert result.segment == "at_risk"
