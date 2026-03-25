"""
╔══════════════════════════════════════════════════════════════════════════╗
║  NexusOS — Predictive Inventory Engine                                   ║
║  File: services/ai/inventory/forecast.py                                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║  WHAT THIS FILE DOES:                                                    ║
║  Uses Facebook Prophet (a machine learning library) to predict how many ║
║  units of a product you'll sell in the next 30 days.                    ║
║                                                                          ║
║  WHY DOES FORECASTING MATTER?                                            ║
║  PROBLEM: You sell Charizard cards. How many should you stock?           ║
║  - Too few → run out → lose $400 sales + angry customers                ║
║  - Too many → $800 tied up in stock that might drop in price            ║
║                                                                          ║
║  SOLUTION: Forecast demand from historical sales data.                  ║
║  If you sold avg 5 cards/day for 90 days, and lead time = 10 days,     ║
║  you should order when you have 5×(10+7) = 85 units left.              ║
║                                                                          ║
║  WHAT IS PROPHET?                                                        ║
║  Developed by Facebook's Core Data Science team.                        ║
║  It decomposed time-series into:                                         ║
║    - Trend: long-term growth or decline                                  ║
║    - Seasonality: weekly/yearly patterns                                 ║
║    - Holiday effects: spikes around events                              ║
║    - Custom regressors: campaign_boost from marketing                   ║
║                                                                          ║
║  HOW IT DIFFERS FROM A SIMPLE AVERAGE:                                  ║
║  Simple avg: "You sold 5/day last 90 days → expect 5/day next 30 days" ║
║  Prophet:    "You sold 5/day but you have a promo next week (+1.5x)    ║
║               and sales always spike on weekends → 8.2/day average"    ║
║                                                                          ║
║  WHAT HAPPENS WITH THE OUTPUT:                                           ║
║  The forecast output goes into:                                          ║
║    1. check_stockout_risk() → urgency level (CRITICAL/HIGH/MEDIUM/LOW) ║
║    2. generate_purchase_order() → a draft PO for merchant approval      ║
║    3. pokemon_events.py → when a dealer event triggers, checks this     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os
import asyncio

# datetime: Python standard library for working with dates and times.
# datetime → represents a specific point in time ("2026-03-21 14:30:00")
# timedelta → represents a DURATION ("14 days" or "3 hours")
from datetime import datetime, timedelta
from typing import Optional

# pandas: Python's most important data analysis library.
# Provides "DataFrame" — a table structure like a spreadsheet.
# We need it because Prophet requires data in a specific DataFrame format.
# Think of DataFrame as a SQLite table in memory, but with powerful analysis methods.
import pandas as pd

# numpy: numerical computing library. Provides fast array operations.
# max() with numpy: np.max([1,2,3]) runs C-speed, not Python-speed.
# Prophet returns numpy arrays, so we import numpy for compatibility.
import numpy as np

# Prophet: the actual forecasting library.
# From: pip install prophet (in requirements.txt)
# Under the hood, Prophet uses Stan (a probabilistic programming language)
# for Bayesian regression. You don't need to understand Stan — Prophet
# abstracts it behind a simple fit()/predict() interface.
from prophet import Prophet


class InventoryForecaster:
    """
    Demand forecasting engine powered by Facebook Prophet.

    DESIGN: Stateless class (no __init__ DB connections).
    We create one instance and call its methods with the data.
    The forecaster doesn't store results — it computes and returns.

    HOW TO USE:
        forecaster = InventoryForecaster()

        # Step 1: Get forecast
        result = forecaster.forecast_demand("prod_abc", sales_history=[
            {"date": "2026-01-01", "units_sold": 5},
            {"date": "2026-01-02", "units_sold": 3},
            ...
        ])
        # result["daily_average_units"] → 4.1

        # Step 2: Check if we'll run out
        risk = forecaster.check_stockout_risk(
            "prod_abc", current_stock=50, open_po_quantity=0,
            daily_avg_demand=4.1, lead_time_days=10
        )
        # risk["urgency"] → "HIGH" (will run out in 12 days)

        # Step 3: If urgent, draft a purchase order
        po = forecaster.generate_purchase_order(
            "prod_abc", "Pokemon Wholesaler", "CHAR-PSA9",
            quantity_needed=100, unit_cost=320.00, lead_time_days=10
        )
        # → goes to approval_queue for merchant to approve
    """

    def __init__(self):
        # How many days into the future we want to forecast.
        # 30 days gives a good planning horizon for most products.
        self.forecast_days = 30

        # How early do we alert before stockout?
        # If we'll sell out in 14 days and lead time is 10 days,
        # we have only 4 days buffer — trigger reorder alert now.
        self.reorder_buffer_days = 14


    def forecast_demand(
        self,
        product_id: str,
        sales_history: list[dict],  # List of {date: "YYYY-MM-DD", units_sold: int} dicts
        upcoming_campaigns: Optional[list[dict]] = None,  # Optional: marketing campaigns to model
    ) -> dict:
        """
        Forecast daily demand for the next 30 days using Prophet ML.

        Args:
            product_id: Shopify product ID (used as label in output only)
            sales_history: List of daily sales records.
                           Minimum 14 data points for Prophet / more is better.
                           Example: [{"date": "2026-01-01", "units_sold": 5}, ...]
            upcoming_campaigns: Optional list of marketing campaigns that boost sales.
                                Example: [{"start": "2026-04-01", "end": "2026-04-07",
                                           "boost_factor": 1.5}]
                                boost_factor=1.5 means "expect 50% more sales during this period"

        Returns:
            Dict with: product_id, forecast_days, total_forecasted_units,
            daily_average_units, peak_daily_units, forecast_generated_at

        DATA QUALITY NOTE:
            Prophet needs at least 14 data points to detect weekly seasonality.
            With fewer, we fall back to simple_average (averaging past sales).
        """
        # Guard: if we have fewer than 14 days of history, use simple average.
        # 14 = minimum for Prophet to detect weekly patterns (2 full weeks).
        if len(sales_history) < 14:
            return self._simple_forecast(product_id, sales_history)

        # ── Step 1: Prepare data in Prophet's required format ─────────────────
        # Prophet REQUIRES a pandas DataFrame with exactly TWO columns:
        #   'ds' → date (Prophet's required name for the "date stamp" column)
        #   'y'  → value to forecast (Prophet's required name for the "target")
        #
        # Our input has "date" and "units_sold" — we rename them to match Prophet.

        df = pd.DataFrame(sales_history)
        # Rename: "date" → "ds", "units_sold" → "y"
        # in-place=False by default, so we reassign to df
        df = df.rename(columns={"date": "ds", "units_sold": "y"})
        # Convert "ds" column from strings ("2026-01-01") to pandas Timestamp objects.
        # Prophet requires actual datetime types, not strings.
        df["ds"] = pd.to_datetime(df["ds"])

        # ── Step 2: Configure the Prophet model ───────────────────────────────
        model = Prophet(
            # seasonality_mode="multiplicative":
            # Means the seasonal effect MULTIPLIES the trend, not adds to it.
            #   Additive:       sales = trend + seasonal_boost  (e.g., +5 units on weekends)
            #   Multiplicative: sales = trend × seasonal_factor (e.g., ×1.5 on weekends)
            # Multiplicative is better for sales data where the magnitude of seasonal
            # variation scales with overall volume (busy stores have bigger spikes).
            seasonality_mode="multiplicative",

            yearly_seasonality=True,   # Captures annual patterns (holiday season, etc.)
            weekly_seasonality=True,   # Captures weekly patterns (weekends vs weekdays)
            daily_seasonality=False,  # We have daily aggregated data, no intra-day patterns

            # changepoint_prior_scale: how flexible the trend line can be.
            # 0.05 = conservative → trend changes gradually, not spiky.
            # Higher (0.5): trend can change sharply between data points (overfitting risk).
            # Lower (0.01): trend barely changes at all (underfitting risk).
            # 0.05 is Facebook's recommended default for most business data.
            changepoint_prior_scale=0.05,
        )

        # ── Step 3: Add campaign regressor (optional) ─────────────────────────
        # Regressors = extra "signals" beyond date that affect sales.
        # We add a "campaign_boost" column: 0 on normal days, boost_factor-1 on campaign days.
        # Example: boost_factor=1.5 → campaign_boost column = 0.5 on those days
        # (We subtract 1 so that 0 = no boost, positive = boost, negative = dip)
        if upcoming_campaigns:
            # Tell Prophet this new column exists as an extra predictor
            model.add_regressor("campaign_boost")
            # Initialize the campaign_boost column to 0.0 for all rows
            df["campaign_boost"] = 0.0
            for campaign in upcoming_campaigns:
                # Create a boolean mask: True where date is within campaign period
                # (df["ds"] >= start) & (df["ds"] <= end) → element-wise AND comparison
                mask = (df["ds"] >= campaign["start"]) & (df["ds"] <= campaign["end"])
                # Set campaign_boost = boost_factor - 1 for days in the campaign
                # If boost_factor=1.5: campaign_boost = 0.5 (50% increase signal)
                df.loc[mask, "campaign_boost"] = campaign.get("boost_factor", 1.5) - 1.0

        # ── Step 4: Train the model ────────────────────────────────────────────
        # model.fit() trains Prophet on our historical data.
        # This is the ML training step — it learns trend + seasonality patterns.
        # Takes ~1-3 seconds depending on data size. OK for an HTTP endpoint.
        model.fit(df)

        # ── Step 5: Generate future dates for prediction ───────────────────────
        # make_future_dataframe() creates a DataFrame of future dates to predict.
        # periods=30 → adds 30 new rows (one per day) after the last training date.
        # The returned DataFrame has a "ds" column with past + future dates.
        future = model.make_future_dataframe(periods=self.forecast_days)

        # If we used campaign_boost as a regressor, we need to set it on the future
        # dates too (Prophet requires all regressor columns in future DataFrame).
        if upcoming_campaigns:
            future["campaign_boost"] = 0.0
            for campaign in upcoming_campaigns:
                mask = (future["ds"] >= campaign["start"]) & (future["ds"] <= campaign["end"])
                future.loc[mask, "campaign_boost"] = campaign.get("boost_factor", 1.5) - 1.0

        # ── Step 6: Generate predictions ──────────────────────────────────────
        # model.predict(future) runs Prophet's forecast on all dates (past + future).
        # Returns a DataFrame with columns:
        #   ds          → the date
        #   yhat        → predicted value (point estimate — e.g., 5.3 units/day)
        #   yhat_lower  → lower bound of 80% confidence interval
        #   yhat_upper  → upper bound of 80% confidence interval (pessimistic demand)
        forecast = model.predict(future)

        # .tail(n): get the last n rows. The last 30 rows are the FUTURE predictions.
        # Everything before that is the fitted values on historical data.
        future_only = forecast.tail(self.forecast_days)

        # Total units we expect to sell in the next 30 days.
        # .sum() adds up the yhat column. max(0, ...) prevents negative forecasts.
        # (Prophet can sometimes predict negative values for very low-volume products;
        # we clamp to 0 since you can't sell negative units.)
        total_forecast = max(0, float(future_only["yhat"].sum()))

        # Average units per day over the forecast period
        daily_avg = total_forecast / self.forecast_days

        # Peak day demand: the maximum daily upper-bound prediction.
        # yhat_upper is the "worst case high demand day" estimate.
        # We use this for safety stock calculations — plan for the peak, not the average.
        peak_day_demand = max(0, float(future_only["yhat_upper"].max()))

        # ── Step 7: Return the result ──────────────────────────────────────────
        return {
            "product_id": product_id,
            "forecast_days": self.forecast_days,
            "total_forecasted_units": round(total_forecast),     # int estimate
            "daily_average_units": round(daily_avg, 2),          # e.g., 4.73 units/day
            "peak_daily_units": round(peak_day_demand),          # worst case single-day peak
            "forecast_generated_at": datetime.utcnow().isoformat() + "Z",  # ISO 8601 timestamp
        }


    def calculate_reorder_point(
        self,
        daily_avg_demand: float,
        lead_time_days: int,
        safety_stock_days: int = 7,  # Default: maintain 7 days of safety buffer
    ) -> int:
        """
        Calculate the Reorder Point (ROP).

        WHAT IS ROP?
        The inventory level that TRIGGERS a new purchase order.
        When stock drops to ROP, it's time to reorder.

        THE FORMULA:
        ROP = (Daily Demand × Lead Time) + Safety Stock
        Safety Stock = Daily Demand × Safety Stock Days

        WHY SAFETY STOCK?
        Lead time is not perfectly predictable. Suppliers run late.
        Demand spikes unexpectedly. Safety stock is a buffer against
        these uncertainties. 7 days = 1 week of protection.

        EXAMPLE:
            daily_avg = 5 cards/day
            lead_time = 10 days
            safety_stock_days = 7

            safety_stock = 5 × 7 = 35 units
            rop = (5 × 10) + 35 = 85 units

            → When stock hits 85 units, order more.
            → By the time the order arrives (10 days), you'll still have 35 units left.

        Args:
            daily_avg_demand: Average units sold per day (from forecast_demand)
            lead_time_days: How many days from ordering to receiving stock
            safety_stock_days: How many days of buffer to maintain (default: 7)

        Returns:
            Integer units — the stock level that should trigger reordering.
        """
        # Calculate minimum safety stock in units
        safety_stock = daily_avg_demand * safety_stock_days
        # Full formula: units consumed during lead time + the safety buffer
        rop = (daily_avg_demand * lead_time_days) + safety_stock
        # max(1, ...) ensures we always have at least 1 unit as minimum ROP.
        # (Prevents edge case of ROP=0 for slow-moving products)
        return max(1, round(rop))


    def check_stockout_risk(
        self,
        product_id: str,
        current_stock: int,      # How many units are physically in stock right now
        open_po_quantity: int,   # Units already ordered (in transit / not yet arrived)
        daily_avg_demand: float, # From forecast_demand()[daily_average_units]
        lead_time_days: int,     # Days from ordering to receiving
    ) -> dict:
        """
        ATP (Available-to-Promise) — determine if we're at risk of stocking out.

        Available-to-Promise is a supply chain metric answering:
        "How many units can we actually promise to sell before we need to reorder?"

        WHY INCLUDE OPEN_PO_QUANTITY?
        If we have 40 units in stock AND 60 on a pending purchase order,
        we're not really "stockout risk" — we just need to wait for the delivery.
        ATP = current_stock + open_po_quantity = 100 units available.

        URGENCY LEVELS:
        CRITICAL: <7 days of stock → ORDER NOW, might need expedited shipping
        HIGH:     7-14 days → Reorder today at standard shipping
        MEDIUM:   14-30 days → Plan reorder this week
        LOW:      30+ days → No action needed

        Args:
            product_id: For identification in the output dict
            current_stock: Units physically in your warehouse/Shopify location
            open_po_quantity: Units already ordered but not yet received
            daily_avg_demand: From forecast_demand() output
            lead_time_days: From supplier contract / historical average

        Returns:
            Dict with all the metrics LogisticsAgent needs to make decisions.
        """
        # Total units we can actually promise before needing to reorder
        available = current_stock + open_po_quantity

        # How many days will our available stock last?
        # max(daily_avg_demand, 0.1) prevents division by zero for zero-demand products.
        # (If demand is 0, we have infinite days of stock — but 0.1 is a safe minimum)
        days_of_stock = available / max(daily_avg_demand, 0.1)

        # Calculate the reorder point (when we should trigger an order)
        reorder_point = self.calculate_reorder_point(daily_avg_demand, lead_time_days)

        # Are we currently at or below the reorder point?
        # (> means we got here by selling down without reordering — urgent!)
        needs_reorder = current_stock <= reorder_point

        # When will we stock out? datetime.utcnow() + timedelta(days=days_of_stock)
        # Example: today=March 21 + 12.3 days = April 2 ≈ stockout date
        stockout_date = datetime.utcnow() + timedelta(days=days_of_stock)

        # Assign urgency tier based on days_of_stock
        if days_of_stock < 7:
            urgency = "CRITICAL"   # Run out this week — emergency reorder needed
        elif days_of_stock < 14:
            urgency = "HIGH"       # Run out in 1-2 weeks — reorder today
        elif days_of_stock < 30:
            urgency = "MEDIUM"     # Run out this month — plan reorder this week
        else:
            urgency = "LOW"        # 30+ days — no immediate action needed

        return {
            "product_id": product_id,
            "current_stock": current_stock,
            "open_po_quantity": open_po_quantity,
            "available_to_promise": available,
            "days_of_stock_remaining": round(days_of_stock, 1),  # e.g., 12.3 days
            "estimated_stockout_date": stockout_date.strftime("%Y-%m-%d"),  # "2026-04-02"
            "reorder_point": reorder_point,
            "needs_reorder": needs_reorder,    # True/False boolean
            "urgency": urgency,                # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
        }


    def generate_purchase_order(
        self,
        product_id: str,
        supplier_name: str,      # e.g., "Pokemon Wholesale Co."
        supplier_sku: str,       # The supplier's part number for this product
        quantity_needed: int,    # How many to order
        unit_cost: float,        # Cost per unit in USD (what we pay the supplier)
        lead_time_days: int,     # How long until delivery
    ) -> dict:
        """
        Generate a DRAFT purchase order for merchant one-click approval.

        WHY DRAFT?
        NexusOS is AUTONOMOUS but NOT RECKLESS. Spending money always requires
        a human to approve. We draft the PO with all details calculated,
        then put it in the approval_queue table with status="pending_merchant_approval".
        The merchant sees it in the Approvals dashboard and clicks ✅ or ❌.

        ONLY AFTER APPROVAL does NexusOS:
        - Send the PO to the supplier (via email or supplier API)
        - Create the purchase record in Shopify/ERP

        This is Human-in-the-Loop (HiTL) for financial decisions.

        WHAT "DRAFT" MEANS:
        status = "pending_merchant_approval" → not yet placed with supplier.
        The po_number starts with "PO-AI-" to clearly mark it as AI-generated.
        The merchant can see "hey, the AI wants to spend $3,200 on Charizard cards"
        and make the final call.

        Args:
            product_id: The Shopify product ID
            supplier_name: Human-readable supplier name
            supplier_sku: Supplier's internal part number for this product
            quantity_needed: How many units to order
            unit_cost: Cost per unit from supplier
            lead_time_days: Delivery time from supplier

        Returns:
            Dict representing the draft PO — goes to approval_queue in PostgreSQL.
        """
        # Calculate expected arrival date
        # timedelta(days=lead_time_days) creates a duration offset
        # Adding to utcnow() gives us the expected arrival datetime
        expected_arrival = datetime.utcnow() + timedelta(days=lead_time_days)

        return {
            "po_type": "draft",   # Not yet a real PO — needs merchant approval
            # PO number format: PO-AI-YYYYMMDD-first8charsOfProductId
            # Example: PO-AI-20260321-prod-abc1
            # strftime("%Y%m%d") formats the date as "20260321"
            "po_number": f"PO-AI-{datetime.utcnow().strftime('%Y%m%d')}-{product_id[:8]}",
            "product_id": product_id,
            "supplier_name": supplier_name,
            "supplier_sku": supplier_sku,
            "quantity": quantity_needed,
            "unit_cost_usd": unit_cost,
            # Total cost = units × per-unit cost, rounded to 2 decimal places
            "total_cost_usd": round(quantity_needed * unit_cost, 2),
            # strftime("%Y-%m-%d") formats datetime as "2026-04-01" (human readable date)
            "expected_arrival": expected_arrival.strftime("%Y-%m-%d"),
            "lead_time_days": lead_time_days,
            "status": "pending_merchant_approval",  # Requires HiTL approval
            "generated_by": "LogisticsAgent",        # For audit: which system created this?
            "generated_at": datetime.utcnow().isoformat() + "Z",  # ISO 8601 timestamp
        }


    def _simple_forecast(self, product_id: str, sales_history: list[dict]) -> dict:
        """
        Fallback forecast when we don't have enough data for Prophet.

        WHEN IS THIS USED?
        When sales_history has fewer than 14 data points.
        New products, recently added to Shopify, won't have 14 days of data yet.

        WHAT IT DOES:
        Simple average: (sum of all units sold) ÷ (number of days)
        Then extrapolates: average × 30 = total_forecasted_units

        It's not as accurate as Prophet but better than returning an error.
        The output includes a "warning" key so callers know this is a rough estimate.

        The underscore `_` prefix means this is a PRIVATE method.
        By convention: only other methods of this class should call it directly.
        External code calls forecast_demand() which calls this internally when needed.

        Args:
            product_id: For the output label
            sales_history: List of sales records (fewer than 14)

        Returns:
            Same dict structure as forecast_demand() but with "method" and "warning" keys.
        """
        # Edge case: no history at all
        if not sales_history:
            return {
                "product_id": product_id,
                "daily_average_units": 0,
                "error": "No sales history",
            }

        # Calculate simple daily average
        # sum() adds up all "units_sold" values; dict.get(key, default) used in case key is missing
        avg = sum(d.get("units_sold", 0) for d in sales_history) / len(sales_history)

        return {
            "product_id": product_id,
            "forecast_days": self.forecast_days,
            "total_forecasted_units": round(avg * self.forecast_days),  # avg × 30 days
            "daily_average_units": round(avg, 2),
            "peak_daily_units": round(avg * 1.5),  # assume peak is 1.5× average
            "method": "simple_average",   # tells callers this is NOT the ML forecast
            "warning": "Insufficient history for ML forecasting (<14 days). Using simple average.",
        }
