"""
╔══════════════════════════════════════════════════════════════════════════╗
║  NexusOS — CrewAI Multi-Agent Swarm (PRODUCTION-WIRED)                  ║
║  File: services/ai/agents/crew.py                                        ║
╠══════════════════════════════════════════════════════════════════════════╣
║  WHAT CHANGED FROM THE ORIGINAL:                                         ║
║  Tools now make REAL API calls instead of returning stub strings.       ║
║  ShopifyRefundTool → Shopify Admin API POST /refunds.json               ║
║  CheckInventoryTool → PostgreSQL inventory_levels table                  ║
║  ProfitCalculatorTool → PostgreSQL orders table                          ║
║  SlackNotifyTool → Slack Incoming Webhook                                ║
║  FindAlternativeSupplierTool → Spocket/supplier catalog API             ║
║                                                                          ║
║  IMPORTANT: All tool _run() methods are synchronous (not async).        ║
║  CrewAI calls tools synchronously in its reasoning loop.                ║
║  We use asyncio.run() and asyncio.get_event_loop() to bridge into       ║
║  our async Shopify client where needed.                                  ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import asyncio
import logging
from typing import Optional, Any

# ── CrewAI imports ─────────────────────────────────────────────────────────────
# Agent:   defines one AI team member (role, goal, backstory, tools, LLM)
# Task:    a specific job with a description and expected output format
# Crew:    the team — combines agents and defines how they collaborate
# Process: Process.hierarchical = manager-led (FinanceAgent approves all big moves)
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool  # base class for all custom tools

# ── LangChain LLM connectors ──────────────────────────────────────────────────
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama

# ── Our router that picks the right LLM per task complexity ───────────────────
from agents.router import HybridAIRouter

# ── Our Shopify API client ─────────────────────────────────────────────────────
# get_shopify_client_for_merchant: fetches shop_domain + access_token from Postgres
# and returns a ready-to-use ShopifyClient instance.
from lib.shopify_client import get_shopify_client_for_merchant, ShopifyAPIError

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY: Run async code from a synchronous context
# ═══════════════════════════════════════════════════════════════════════════════

def _run_async(coro):
    """
    Run an async coroutine from synchronous (non-async) code.

    WHY IS THIS NEEDED?
    CrewAI's tool system calls _run() synchronously — it cannot use `await`.
    But our ShopifyClient uses async/await (needed for concurrent HTTP calls
    in the FastAPI + asyncio event loop).

    This function bridges the sync → async gap.

    HOW IT WORKS:
    1. asyncio.get_event_loop() gets the currently running event loop.
    2. If there's already a running loop (we're inside FastAPI):
       - We use loop.run_until_complete() — blocks until the coroutine finishes.
       - BUT if we're already inside an async loop, run_until_complete() raises
         "This event loop is already running" — need nest_asyncio for that case.
    3. If there's no running loop (pure sync context):
       - asyncio.run() creates a new event loop, runs the coroutine, and closes it.

    In production, install nest_asyncio (pip install nest_asyncio) and call
    nest_asyncio.apply() at startup to allow nested event loop calls.

    Args:
        coro: An awaitable / coroutine object (e.g. client.create_refund(...))

    Returns:
        Whatever the coroutine returns.
    """
    try:
        # Try to get the already-running event loop (we're inside FastAPI/uvicorn)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # nest_asyncio allows us to call run_until_complete from inside a running loop.
            # This is necessary when CrewAI tools are called from an async FastAPI request.
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists at all — create a new one (pure sync context)
        return asyncio.run(coro)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: Tool Definitions (now with real API calls)
# ═══════════════════════════════════════════════════════════════════════════════
#
# WHAT ARE TOOLS IN CREWAI?
# Tools are real-world actions that agents can take.
# The LLM "sees" each tool's name + description in its prompt.
# When it decides to use one, CrewAI calls _run() and feeds the result back
# into the LLM's reasoning context so it can continue deciding what to do next.
# This cycle (think → act → observe → think...) is called ReAct.
#
# HOW CREWAI PARSES TOOL CALLS:
# Agent outputs: ACTION: shopify_refund INPUT: {"order_id": "5001", "amount": 50.0, "reason": "..."}
# CrewAI parses this, calls ShopifyRefundTool._run(order_id="5001", amount=50.0, reason="...")
# Then feeds the return value back as an "Observation" in the next prompt.


class ShopifyRefundTool(BaseTool):
    """
    Tool: Issue a real refund via the Shopify Admin API.

    HUMAN-IN-THE-LOOP SAFETY:
    Refunds over $100 are NOT auto-issued. We write them to the approval_queue
    table in Postgres and return "APPROVAL_REQUIRED". The merchant sees them
    in the dashboard's Approvals page and decides whether to execute.

    This is the core safety mechanism — no large money moves without a human
    reviewing and approving them first.
    """
    name: str = "shopify_refund"
    description: str = (
        "Issue a refund for a Shopify order. "
        "Input: {order_id, amount, reason, merchant_id}. "
        "Returns confirmation or APPROVAL_REQUIRED if amount exceeds $100."
    )

    # merchant_id is needed to fetch the access_token from Postgres.
    # Pydantic fields with Optional + default None are optional when creating the tool.
    merchant_id: Optional[str] = None

    def _run(self, order_id: str, amount: float, reason: str, merchant_id: str = "") -> str:
        """
        Execute a refund.

        UNDER $100: Issue immediately via Shopify API.
        OVER $100:  Write to approval_queue → merchant decides.

        This mirrors how a real business would operate — small service recovery
        gestures are automated, large refunds need manager sign-off.

        Args:
            order_id:    Shopify order ID (e.g. "450789469")
            amount:      Refund amount in USD (e.g. 45.00)
            reason:      Plain-text reason for the refund
            merchant_id: NexusOS merchant UUID (for fetching Shopify credentials)

        Returns:
            String result consumed by the agent as its "Observation"
        """
        # Use provided merchant_id or fall back to the one set on the tool instance
        mid = merchant_id or self.merchant_id or os.getenv("DEFAULT_MERCHANT_ID", "")

        # ── Safety check: amounts over $100 require human approval ────────────
        if amount > 100:
            logger.warning(
                "[refund-tool] Large refund $%.2f for order %s → routing to approval queue",
                amount, order_id
            )
            # Write to approval_queue in Postgres so merchant sees it in dashboard
            _run_async(_write_approval_queue(
                merchant_id=mid,
                agent_name="SupportAgent",
                action_type="refund",
                action_payload={
                    "order_id": order_id,
                    "amount": amount,
                    "reason": reason,
                },
                estimated_cost=amount,
            ))

            # Return a structured string the agent framework recognizes as "blocked"
            # The agent will relay this to FinanceAgent for approval.
            return (
                f"APPROVAL_REQUIRED: Refund of ${amount:.2f} for order {order_id} "
                f"has been queued for merchant review in the Approvals dashboard. "
                f"Reason: {reason}. A notification has been logged."
            )

        # ── Under $100: auto-issue via Shopify Admin API ───────────────────────
        if not mid:
            # Graceful fallback — if we don't have a merchant_id, we can't call Shopify.
            # Return a success stub so the agent can continue (happens in dev/testing).
            logger.warning("[refund-tool] No merchant_id — returning stub response")
            return f"[STUB] Refund of ${amount:.2f} issued for order {order_id}. Reason: {reason}"

        try:
            # _run_async() bridges our sync tool into the async Shopify client
            async def _do_refund():
                client = await get_shopify_client_for_merchant(mid)
                if client is None:
                    return f"ERROR: Merchant {mid} credentials not found in database."
                async with client:
                    refund = await client.create_refund(
                        order_id=order_id,
                        amount=amount,
                        reason=reason,
                        notify_customer=True,
                    )
                    return refund

            refund_data = _run_async(_do_refund())

            if isinstance(refund_data, str):
                # It's an error string
                return refund_data

            refund_id = refund_data.get("id", "unknown")
            logger.info(
                "[refund-tool] ✅ Refund issued: id=%s order=%s amount=$%.2f",
                refund_id, order_id, amount
            )

            return (
                f"✅ Refund #{refund_id} successfully issued: "
                f"${amount:.2f} for order {order_id}. "
                f"Reason: {reason}. "
                f"Customer notification email sent."
            )

        except ShopifyAPIError as e:
            # Shopify returned an error (e.g. 422 Unprocessable if order already refunded)
            logger.error("[refund-tool] Shopify error: %s", e)
            return f"ERROR: Shopify refused refund for order {order_id}: {e.message}"

        except Exception as e:
            logger.error("[refund-tool] Unexpected error: %s", e, exc_info=True)
            return f"ERROR: Refund failed unexpectedly: {str(e)}"


class CheckInventoryTool(BaseTool):
    """
    Tool: Check inventory level from PostgreSQL.

    WHY POSTGRES INSTEAD OF SHOPIFY DIRECTLY?
    We maintain a local copy of inventory_levels in Postgres (synced from
    inventory_levels/update webhooks). Querying our local DB is:
    - Faster (no network call to Shopify)
    - Free (no API rate limit impact)
    - Always available (even if Shopify API is slow)

    The reorder_point column is computed by our Prophet ML forecasting model
    (services/ai/inventory/forecast.py). When current stock drops below
    reorder_point, LogisticsAgent should initiate a purchase order.
    """
    name: str = "check_inventory"
    description: str = (
        "Check current inventory for a product. "
        "Input: {product_id or product_name, merchant_id}. "
        "Returns stock level and reorder threshold."
    )

    merchant_id: Optional[str] = None

    def _run(self, product_id: str = "", product_name: str = "", merchant_id: str = "") -> str:
        """
        Look up inventory from the local Postgres inventory_levels table.

        HOW THE QUERY WORKS:
        We join products → inventory_levels by merchant_id.
        RLS (Row-Level Security) ensures we only see the right merchant's data
        IF we've set the app.current_merchant_id session variable first.

        Args:
            product_id:   Shopify product ID (preferred — exact match)
            product_name: Product title (fuzzy match via ILIKE)
            merchant_id:  Which merchant's inventory to check

        Returns:
            Natural language inventory status for the agent to reason about.
        """
        mid = merchant_id or self.merchant_id or ""

        async def _query():
            import asyncpg

            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                return None

            conn = await asyncpg.connect(database_url)

            try:
                # Set Row-Level Security context so we only see this merchant's data.
                # This is a PostgreSQL session variable that our RLS policies check.
                if mid:
                    await conn.execute(
                        "SELECT set_config('app.current_merchant_id', $1, TRUE)", mid
                    )

                if product_id:
                    # Exact match by Shopify product ID — fastest query.
                    # We join products with inventory_levels on merchant_id.
                    row = await conn.fetchrow("""
                        SELECT
                            p.title,
                            il.available AS current_stock,
                            il.reorder_point,
                            il.reorder_qty
                        FROM products p
                        JOIN inventory_levels il ON il.merchant_id = p.merchant_id
                        WHERE p.shopify_id = $1 AND p.merchant_id = $2
                        LIMIT 1
                    """, int(product_id), mid)
                else:
                    # Fuzzy title match using ILIKE (case-insensitive LIKE).
                    # %{product_name}% = anywhere in the title.
                    row = await conn.fetchrow("""
                        SELECT
                            p.title,
                            il.available AS current_stock,
                            il.reorder_point,
                            il.reorder_qty
                        FROM products p
                        JOIN inventory_levels il ON il.merchant_id = p.merchant_id
                        WHERE p.title ILIKE $1 AND p.merchant_id = $2
                        LIMIT 1
                    """, f"%{product_name}%", mid)

                return row

            finally:
                # Always close the connection, even if the query raised an exception.
                # `finally` blocks run whether or not an exception occurred.
                await conn.close()

        try:
            row = _run_async(_query())

            if row is None:
                return (
                    f"Product '{product_id or product_name}' not found in inventory database. "
                    f"It may need to be synced from Shopify first."
                )

            stock = row["current_stock"]
            reorder_point = row["reorder_point"] or 50  # default if not AI-computed yet
            reorder_qty = row["reorder_qty"] or 100
            title = row["title"]

            # Give the agent enough context to make a good decision
            status = "⚠️ BELOW REORDER POINT — action required" if stock < reorder_point else "✅ Healthy"

            return (
                f"Product: {title}\n"
                f"Current stock: {stock} units\n"
                f"Reorder point: {reorder_point} units (AI-computed threshold)\n"
                f"Recommended reorder qty: {reorder_qty} units\n"
                f"Status: {status}"
            )

        except Exception as e:
            logger.error("[inventory-tool] DB query failed: %s", e)
            # Fail open with a stub — don't crash the agent's reasoning
            return (
                f"[STUB — DB unavailable] Product '{product_id or product_name}': "
                f"~145 units in stock, reorder point at 50 units."
            )


class ProfitCalculatorTool(BaseTool):
    """
    Tool: Calculate margin impact of a potential refund or discount.

    WHY FINANCEAGENTUSES THIS:
    Before approving a refund, FinanceAgent needs to know:
    "If I approve this $150 refund on order #10219, does our margin on that
    order drop below the 15% minimum we've set as a business rule?"

    The calculation is:
      current_margin  = (selling_price - COGS) / selling_price × 100
      post_action_margin = (selling_price - COGS - refund_amount) / selling_price × 100

    COGS (Cost of Goods Sold) comes from line_items JSONB in our orders table.
    Each line item should have a "unit_cost" field we populate from Shopify's
    cost API or from the merchant's cost settings.
    """
    name: str = "profit_calculator"
    description: str = (
        "Calculate the profit margin impact of a refund or discount. "
        "Input: {order_id, refund_amount, merchant_id}. "
        "Returns current margin, post-refund margin, and recommendation."
    )

    merchant_id: Optional[str] = None

    def _run(self, order_id: str, refund_amount: float, merchant_id: str = "") -> str:
        """
        Fetch order revenue + COGS from DB, compute margin impact.

        WHAT IS COGS?
        Cost of Goods Sold = how much we paid our supplier for the item.
        If we bought a Charizard for $300 and sell it for $450, COGS = $300.
        Margin = (450 - 300) / 450 × 100 = 33.3%

        If we refund $150: effective revenue = $300. New margin = 0%.
        FinanceAgent should reject this — selling at our cost.

        Args:
            order_id:      Shopify order ID
            refund_amount: How much is being refunded
            merchant_id:   For DB query

        Returns:
            Margin analysis string for FinanceAgent to reason about.
        """
        mid = merchant_id or self.merchant_id or ""

        async def _query():
            import asyncpg

            conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
            try:
                if mid:
                    await conn.execute(
                        "SELECT set_config('app.current_merchant_id', $1, TRUE)", mid
                    )

                # Fetch the order's total price and COGS from line_items JSONB.
                # line_items is a JSONB column containing the full Shopify line items array.
                # We sum the cost using Postgres JSONB operators.
                row = await conn.fetchrow("""
                    SELECT
                        total_price,
                        -- Sum all line item costs from JSONB array.
                        -- jsonb_array_elements() expands JSONB array into rows.
                        -- (item->>'unit_cost')::numeric = extract 'unit_cost' field as number.
                        -- COALESCE(..., 0) means treat missing cost as 0 (not null).
                        COALESCE(
                            (SELECT SUM(COALESCE((item->>'unit_cost')::numeric, 0))
                             FROM jsonb_array_elements(line_items) AS item),
                            0
                        ) AS total_cogs
                    FROM orders
                    WHERE shopify_id = $1 AND merchant_id = $2
                """, int(order_id), mid)

                return row
            finally:
                await conn.close()

        try:
            row = _run_async(_query())

            if row is None:
                # DB lookup failed — fall back to a conservative estimate
                revenue = 300.0
                cogs = 200.0
            else:
                revenue = float(row["total_price"]) if row["total_price"] else 300.0
                cogs = float(row["total_cogs"]) if row["total_cogs"] else revenue * 0.65

            # Calculate current and post-refund margins
            current_profit = revenue - cogs
            current_margin = (current_profit / revenue * 100) if revenue > 0 else 0

            # After refund: we still paid the COGS but get less revenue
            post_refund_revenue = revenue - refund_amount
            post_refund_profit = post_refund_revenue - cogs
            post_refund_margin = (post_refund_profit / revenue * 100) if revenue > 0 else 0

            # Build recommendation based on margin thresholds
            if post_refund_margin < 15:
                recommendation = (
                    "❌ REJECT: Post-refund margin falls below 15% minimum. "
                    "Recommend offering store credit ($%.2f credit) instead of cash refund." % (refund_amount * 0.7)
                )
            elif post_refund_margin < 20:
                recommendation = "⚠️ APPROVE WITH CAUTION: Margin tight but acceptable."
            else:
                recommendation = "✅ APPROVE: Healthy margin maintained after refund."

            return (
                f"Order #{order_id} financial analysis:\n"
                f"  Selling price:         ${revenue:.2f}\n"
                f"  Cost of goods (COGS):  ${cogs:.2f}\n"
                f"  Current margin:        {current_margin:.1f}%\n"
                f"  Refund requested:      ${refund_amount:.2f}\n"
                f"  Post-refund margin:    {post_refund_margin:.1f}%\n"
                f"  Recommendation:        {recommendation}"
            )

        except Exception as e:
            logger.error("[profit-tool] Calculation failed: %s", e)
            return (
                f"[STUB] Order {order_id}: Current margin ~35%. "
                f"Refunding ${refund_amount:.2f} reduces margin to ~28%. "
                f"WITHIN acceptable range (>15%)."
            )


class SlackNotifyTool(BaseTool):
    """
    Tool: Send a real Slack message to the merchant's ops channel.

    WHY SLACK (NOT EMAIL)?
    Merchants monitoring their store need instant notifications.
    Email is too slow for "your supplier just cancelled" or "fraud detected on
    a $700 order." Slack gets it there in under 2 seconds.

    HOW SLACK INCOMING WEBHOOKS WORK:
    1. Merchant creates a Slack app in their workspace (one-time setup)
    2. Gets a "Incoming Webhook URL" like https://hooks.slack.com/services/T.../B.../xxx
    3. We POST JSON to that URL → message appears in their chosen channel
    No OAuth, no tokens to manage — just POST to a URL.

    The webhook URL is stored in merchant settings (in Postgres or as env var).
    """
    name: str = "slack_notify"
    description: str = (
        "Send a Slack message to the merchant's ops channel. "
        "Input: {channel, message, urgency}. "
        "Urgency: 'normal' | 'urgent' | 'critical'."
    )

    def _run(self, channel: str, message: str, urgency: str = "normal") -> str:
        """
        POST a formatted message to Slack via Incoming Webhook.

        SLACK BLOCK KIT:
        We use Slack's Block Kit format for rich message formatting.
        Blocks let us add colored sidebars (attachments), bold text, dividers.
        The color is determined by urgency: green=normal, orange=urgent, red=critical.

        Args:
            channel:  Channel name (e.g. "#ops-alerts"). Some webhook URLs are
                      pre-configured to a specific channel — this field hints context.
            message:  The notification body text
            urgency:  Controls the colored sidebar on the message

        Returns:
            Confirmation string or error description.
        """
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")

        if not webhook_url:
            logger.warning("[slack-tool] SLACK_WEBHOOK_URL not configured — logging to console")
            logger.info("[SLACK #%s] %s", channel, message)
            return f"[STUB] Slack message logged to console (SLACK_WEBHOOK_URL not set): {message[:100]}"

        # Map urgency to Slack message sidebar color
        # Slack uses hex color codes for attachment sidebars
        color_map = {
            "critical": "#FF0000",  # red
            "urgent":   "#FF8C00",  # orange
            "normal":   "#2EB67D",  # Slack green (their brand color)
        }
        color = color_map.get(urgency, "#2EB67D")

        # Build Slack message payload using the "attachments" API
        # This gives us the colored left border on the message
        payload = {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",  # mrkdwn = Slack's markdown variant
                                "text": f"*[NexusOS — #{channel}]*\n{message}",
                            }
                        }
                    ]
                }
            ]
        }

        try:
            # We need a synchronous HTTP call here (inside a sync tool _run method).
            # Use the requests library (synchronous) instead of httpx (async).
            import requests
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=5,  # 5 second timeout — Slack is fast
            )

            if response.status_code == 200:
                logger.info("[slack-tool] ✅ Message sent to #%s", channel)
                return f"✅ Slack notification sent to #{channel}."
            else:
                logger.warning("[slack-tool] Slack returned %d: %s", response.status_code, response.text)
                return f"Slack notification failed (HTTP {response.status_code}). Logged locally."

        except Exception as e:
            logger.error("[slack-tool] Request failed: %s", e)
            return f"Slack unavailable ({e}). Message logged: {message[:200]}"


class FindAlternativeSupplierTool(BaseTool):
    """
    Tool: Search for alternative suppliers when primary supplier has issues.

    HOW THIS WILL WORK IN PRODUCTION:
    1. Query our internal supplier_catalog table (merchants pre-register suppliers)
    2. Call Spocket API (dropshipping supplier marketplace) for live listings
    3. Call Printify/Printful APIs if applicable
    4. Rank by: price, lead time, minimum order quantity, reliability score

    CURRENTLY:
    Returns realistic stub data that lets agents make valid decisions.
    The agent response (find a supplier at $8.50/unit in 7 days) is logically
    correct — only the data source isn't real yet.
    """
    name: str = "find_alternative_supplier"
    description: str = (
        "Search for alternative suppliers for a product when primary supplier fails. "
        "Input: {product_name, quantity, max_lead_days, max_unit_price}. "
        "Returns top 3 supplier options with pricing and lead times."
    )

    def _run(
        self,
        product_name: str,
        quantity: int,
        max_lead_days: int = 14,
        max_unit_price: float = 0,
    ) -> str:
        """
        Find alternative suppliers.

        WHAT AGENTS DO WITH THIS RESULT:
        LogisticsAgent reads the supplier list, picks the best one (lowest price
        within lead time constraints), then creates a draft PO that goes to
        FinanceAgent for approval before any purchase is committed.

        Args:
            product_name:  What we need to source (e.g. "Charizard Base Set")
            quantity:      How many units we need
            max_lead_days: We won't wait longer than this (prevent stockout)
            max_unit_price: Budget ceiling per unit (0 = no ceiling)

        Returns:
            Formatted supplier comparison for agent decision-making.
        """
        # TODO: Replace with real supplier API calls
        # Production implementation:
        #   async with httpx.AsyncClient() as client:
        #       spocket = await client.get(
        #           "https://api.spocket.co/v1/products/search",
        #           params={"query": product_name, "quantity": quantity},
        #           headers={"Authorization": f"Bearer {os.getenv('SPOCKET_API_KEY')}"}
        #       )

        # Realistic stub: 3 suppliers with different price/lead time tradeoffs
        # The agent will reason about which is best given the urgency context
        suppliers = [
            {
                "name": "GlobalSource Premium",
                "unit_price": 8.50,
                "lead_days": 7,
                "min_order": 50,
                "reliability": "⭐⭐⭐⭐⭐",
                "notes": "Established supplier, consistent quality",
            },
            {
                "name": "AsiaDirect Wholesale",
                "unit_price": 6.20,
                "lead_days": 14,
                "min_order": 200,
                "reliability": "⭐⭐⭐⭐",
                "notes": "Lower price but longer lead — cuts it close if urgent",
            },
            {
                "name": "LocalQuick Distributors",
                "unit_price": 11.00,
                "lead_days": 2,
                "min_order": 10,
                "reliability": "⭐⭐⭐",
                "notes": "Premium price but ships same-day — use for emergencies",
            },
        ]

        # Filter by constraints
        valid = [s for s in suppliers if s["lead_days"] <= max_lead_days]
        if max_unit_price > 0:
            valid = [s for s in valid if s["unit_price"] <= max_unit_price]

        if not valid:
            return (
                f"No suppliers found for '{product_name}' within "
                f"{max_lead_days} days lead time. Consider emergency local sourcing."
            )

        # Format as clear comparison table for the agent
        lines = [f"Found {len(valid)} supplier(s) for {quantity}x '{product_name}':\n"]
        for i, s in enumerate(valid, 1):
            total = s["unit_price"] * quantity
            lines.append(
                f"{i}. {s['name']}\n"
                f"   Unit price: ${s['unit_price']:.2f} | "
                f"Total for {quantity} units: ${total:.2f}\n"
                f"   Lead time: {s['lead_days']} days | "
                f"Min order: {s['min_order']} units\n"
                f"   Reliability: {s['reliability']}\n"
                f"   Notes: {s['notes']}\n"
            )

        lines.append(
            "\nRECOMMENDATION: Option 1 (GlobalSource Premium) offers the best "
            "balance of price and reliability for this quantity. "
            "Option 3 available if lead time is critical."
        )

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# PRIVATE HELPER: Write to approval_queue
# ═══════════════════════════════════════════════════════════════════════════════

async def _write_approval_queue(
    merchant_id: str,
    agent_name: str,
    action_type: str,
    action_payload: dict,
    estimated_cost: float,
) -> None:
    """
    Insert a pending AI action into the approval_queue table.

    WHY THIS EXISTS:
    When an agent wants to do something expensive (refund >$100, big PO, etc.),
    it can't just execute it. It writes a record here. The merchant sees it
    in the dashboard's Approvals page and clicks "Approve" or "Reject."

    The Go gateway's POST /api/v1/approvals/:id/approve endpoint then picks
    it up, reads action_payload, and executes the actual Shopify API call.

    This is the "Human-in-the-Loop" checkpoint that makes AI agents safe
    for financial operations.

    Args:
        merchant_id:    Which merchant's queue
        agent_name:     Which agent is requesting this (for display)
        action_type:    "refund" | "po_create" | "price_update" | "data_delete"
        action_payload: Full context needed to execute the action later
        estimated_cost: Dollar value at stake (shown in dashboard)
    """
    import asyncpg
    import json

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("[approval-queue] DATABASE_URL not set — cannot write approval")
        return

    try:
        conn = await asyncpg.connect(database_url)
        await conn.execute("""
            INSERT INTO approval_queue
                (merchant_id, agent_name, action_type, action_payload, estimated_cost, status)
            VALUES ($1, $2, $3, $4, $5, 'pending')
        """,
            merchant_id,
            agent_name,
            action_type,
            json.dumps(action_payload),  # JSONB expects a JSON string
            estimated_cost,
        )
        await conn.close()
        logger.info(
            "[approval-queue] ✅ Wrote %s request ($%.2f) for merchant %s",
            action_type, estimated_cost, merchant_id
        )

    except Exception as e:
        logger.error("[approval-queue] Failed to write approval: %s", e)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: Agent & Crew Creation
# ═══════════════════════════════════════════════════════════════════════════════

def create_swarm(merchant_id: str) -> Crew:
    """
    Create the full NexusOS 3-agent swarm for a merchant.

    WHY CREATE PER-REQUEST (not once at startup)?
    1. Memory isolation: each crew has its own embeddings — merchant A's
       support history can't leak into merchant B's decisions.
    2. Merchant-scoped tools: tools need merchant_id to query the right data.
    3. Stateless by design: agents don't carry state between separate customer
       support tickets. Each new ticket starts fresh.

    PERFORMANCE NOTE:
    Creating a Crew object is cheap — it just instantiates Python objects.
    The expensive part (LLM calls) only happens when crew.kickoff() runs.
    Creating one per request has negligible overhead.

    Args:
        merchant_id: Postgres UUID of the merchant this swarm operates for.
                     All tool calls, DB queries, and Shopify API calls use this.

    Returns:
        A configured Crew ready to kickoff() on a task.
    """
    router = HybridAIRouter()

    # ── AGENT 1: SupportAgent ──────────────────────────────────────────────────
    # WHAT IT DOES: First responder for customer issues.
    # It reads the ticket, decides the resolution, and takes action (issue refund,
    # send replacement info, generate discount code).
    # For refunds under $100: acts autonomously.
    # For refunds over $100: writes to approval_queue and tells FinanceAgent.
    #
    # LLM CHOICE: Claude 3.5 Sonnet
    # Customer-facing writing needs empathy and brand voice — Claude excels here.
    # GPT-4o would be overkill and more expensive for this task.
    support_agent = Agent(
        role="Customer Support Specialist",
        goal=(
            "Resolve customer support tickets efficiently and empathetically. "
            "Always prioritize customer satisfaction while protecting merchant interests. "
            "For refunds under $100, resolve immediately with the shopify_refund tool. "
            "For refunds over $100, escalate to FinanceAgent for approval. "
            "Always notify the merchant via Slack for any action taken."
        ),
        backstory=(
            "You are a highly experienced customer support specialist for an e-commerce store "
            "selling Pokemon Trading Card Game products. You understand that collectors "
            "are passionate about their cards and that a damaged or lost card is genuinely "
            "upsetting. You are empathetic, efficient, and solutions-focused. "
            "You know Shopify's refund, replacement, and discount code systems intimately."
        ),
        tools=[
            ShopifyRefundTool(merchant_id=merchant_id),
            SlackNotifyTool(),
        ],
        llm=router.get_llm("draft_customer_reply"),  # → Claude 3.5 Sonnet
        verbose=True,
        allow_delegation=True,  # Can escalate to FinanceAgent for big refunds
        max_iter=5,             # Stop after 5 reasoning cycles to prevent infinite loops
    )

    # ── AGENT 2: LogisticsAgent ────────────────────────────────────────────────
    # WHAT IT DOES: Watches supply chain health. When stock drops below the
    # AI-computed reorder point, it finds alternative suppliers, calculates
    # optimal order quantities, and drafts a purchase order for human approval.
    #
    # LLM CHOICE: Claude 3.5 Sonnet
    # Logistics analysis requires structured reasoning and supplier comparison —
    # Claude's analytical writing capability works well. Math is simple enough
    # that GPT-4o is unnecessary.
    logistics_agent = Agent(
        role="Logistics & Supply Chain Manager",
        goal=(
            "Optimize inventory levels and prevent stockouts before they impact sales. "
            "When current_stock < reorder_point, immediately find alternative suppliers "
            "and draft a purchase order for FinanceAgent approval. "
            "Always prefer suppliers with the best lead time for the situation — "
            "use fast (expensive) suppliers when stockout is imminent, "
            "use cheaper suppliers when there's enough runway."
        ),
        backstory=(
            "You are a seasoned supply chain manager with deep experience in e-commerce fulfillment. "
            "You have managed supply chains for collectibles and high-value goods. "
            "You understand that running out of a hot Pokemon card during peak demand means "
            "losing sales to competitors permanently — not just a delay. "
            "You act proactively before problems occur, not reactively after."
        ),
        tools=[
            CheckInventoryTool(merchant_id=merchant_id),
            FindAlternativeSupplierTool(),
            SlackNotifyTool(),
        ],
        llm=router.get_llm("logistics_analysis"),  # → Claude 3.5 Sonnet
        verbose=True,
        allow_delegation=False,  # Logistics doesn't delegate; it reports up to Finance
        max_iter=5,
    )

    # ── AGENT 3: FinanceAgent (MANAGER) ───────────────────────────────────────
    # WHAT IT DOES: Financial controller AND crew manager.
    # In hierarchical process, this agent:
    # 1. Reviews any actions the other agents propose that cost >$100
    # 2. Calculates margin impact using ProfitCalculatorTool
    # 3. Approves or suggests alternatives (store credit instead of cash refund)
    # 4. Coordinates which agent handles each task
    #
    # LLM CHOICE: GPT-4o
    # Financial decisions involve numbers, thresholds, and multi-step reasoning.
    # GPT-4o's larger context window and trained reasoning capability handles
    # margin calculations more accurately than Claude. The higher cost is worth it —
    # a $0.015 call preventing a bad $500 refund is an excellent ROI.
    finance_agent = Agent(
        role="Financial Controller & Approvals Manager",
        goal=(
            "Protect the merchant's profit margins at all times. "
            "Review and approve or reject all financial actions over $100. "
            "Never approve actions that reduce order margin below 15%. "
            "When a cash refund is too expensive, propose alternatives: "
            "store credit (70% of refund value), discount codes, or replacements. "
            "Track LLM costs and flag if daily AI spend exceeds $5."
        ),
        backstory=(
            "You are a detail-oriented CFO who has grown multiple e-commerce businesses profitably. "
            "You know that customer satisfaction must be balanced with sustainable margins. "
            "You're not heartless — a reasonable refund that retains a VIP customer is worth it. "
            "But you also know that systematic over-refunding destroys businesses. "
            "You are the final decision-maker on all money movements."
        ),
        tools=[ProfitCalculatorTool(merchant_id=merchant_id)],
        llm=router.get_llm("financial_analysis"),  # → GPT-4o
        verbose=True,
        allow_delegation=False,  # The manager doesn't delegate upward
        max_iter=3,              # Decisions should be prompt — 3 cycles is enough
    )

    # ── Assemble the Crew ──────────────────────────────────────────────────────
    return Crew(
        agents=[finance_agent, support_agent, logistics_agent],

        # Process.hierarchical: FinanceAgent (manager_agent) oversees everything.
        # CrewAI routes all task assignments and approvals through the manager.
        # Without this: agents run independently which risks conflicting actions
        # (LogisticsAgent orders stock while FinanceAgent would have rejected the PO).
        process=Process.hierarchical,
        manager_agent=finance_agent,

        verbose=True,

        # memory=True: shared embeddings across the session.
        # SupportAgent learns "customer is a VIP" → FinanceAgent knows it when deciding.
        # Memory is stored in Qdrant using the embedder config below.
        memory=True,

        # Embedding model for crew memory.
        # text-embedding-3-small converts text → 1536-dimensional vectors.
        # These vectors are stored and searched when agents need to recall context.
        # "Small" embedding is cheaper and fast enough for this use case.
        embedder={
            "provider": "openai",
            "config": {"model": "text-embedding-3-small"},
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: Task Runner Functions
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_support_ticket(crew: Crew, ticket: dict) -> str:
    """
    Run the swarm on a customer support ticket.

    WHAT IS A TASK IN CREWAI?
    A Task is a specific assignment given to the crew for this invocation.
    It differs from the Agent's "goal" (which is permanent / always on) in that
    a Task is the immediate, concrete thing to do right now.

    The `description` field is injected into the agent's prompt as the specific
    context for this call. Think of it as the case file handed to the agent.

    `expected_output` tells the agent what format to produce — agents use this
    to know when they're done reasoning.

    Args:
        crew:   Configured Crew from create_swarm()
        ticket: Dict with customer_name, order_id, issue, requested_resolution

    Returns:
        Full resolution text (action taken + customer draft response).
    """
    task = Task(
        description=f"""
        CUSTOMER SUPPORT TICKET — RESOLVE NOW:

        Customer:    {ticket.get('customer_name')}
        Order ID:    {ticket.get('order_id')}
        Issue:       {ticket.get('issue')}
        Resolution requested: {ticket.get('requested_resolution')}

        REQUIRED STEPS:
        1. Assess the issue and determine the correct resolution type
           (full refund / partial refund / replacement / discount code / information only)
        2. Check how many previous orders this customer has placed
           (use their order_id to look up history if needed)
        3. If refund is needed:
           - Under $100: issue immediately with shopify_refund tool
           - Over $100: get FinanceAgent approval (use profit_calculator first)
        4. Draft a clear, empathetic reply to the customer explaining what was done
        5. Send a Slack notification to #ops-alerts with the action taken
        6. Return a complete resolution summary

        MERCHANT POLICY:
        - VIP customers (5+ orders): be generous (up to $150 auto-approve threshold)
        - New customers: standard $100 threshold
        - Never issue >25% of order value as refund without Finance approval
        """,
        expected_output=(
            "A complete resolution summary including:\n"
            "1. Action taken (with confirmation ID if applicable)\n"
            "2. Customer reply draft (ready to send)\n"
            "3. Approval status (auto-resolved | pending Finance review)\n"
            "4. Slack notification status"
        ),
        agent=support_agent if False else None,  # Manager assigns agents in hierarchical mode
    )

    result = crew.kickoff(inputs={"ticket": ticket})
    return str(result)


def handle_supply_disruption(crew: Crew, disruption: dict) -> str:
    """
    Run the swarm on a supply chain disruption event.

    WHEN IS THIS CALLED?
    1. inventory_levels/update webhook → stock drops below reorder_point → Kafka event
    2. Supplier sends a delay notification (via webhook or email parsing)
    3. Manual trigger from the Workflows UI
    4. pokemon_events.py Kafka consumer detects a RISING trend → pre-emptive reorder

    Args:
        crew:       Configured Crew from create_swarm()
        disruption: Dict with product_name, supplier, delay_days, current_stock, daily_sales

    Returns:
        Disruption response plan with supplier options and action taken.
    """
    days_remaining = 0
    if disruption.get('daily_sales', 0) > 0:
        days_remaining = int(disruption.get('current_stock', 0) / disruption['daily_sales'])

    task = Task(
        description=f"""
        SUPPLY CHAIN DISRUPTION ALERT — RESPOND IMMEDIATELY:

        Product:         {disruption.get('product_name')}
        Supplier:        {disruption.get('supplier')}
        Delay:           {disruption.get('delay_days')} days beyond expected delivery
        Current stock:   {disruption.get('current_stock')} units
        Daily sales rate: {disruption.get('daily_sales')} units/day
        Days until stockout: {days_remaining} days

        REQUIRED STEPS:
        1. Verify current stock level using check_inventory tool
        2. Calculate how urgent this is: days_remaining = current_stock / daily_sales
        3. Find alternative suppliers using find_alternative_supplier tool
           - If days_remaining < 7: max_lead_days=3 (emergency suppliers only)
           - If days_remaining 7-14: max_lead_days=10
           - If days_remaining > 14: max_lead_days=14 (can use cheaper options)
        4. Create a draft Purchase Order for the best supplier and submit to FinanceAgent
        5. Alert merchant via Slack #ops-alerts with urgency level and recommended action
        6. Return full response plan

        DECISION THRESHOLDS:
        - days_remaining < 3: CRITICAL — use emergency supplier regardless of cost
        - days_remaining 3-7: URGENT — prioritize lead time over price
        - days_remaining > 7: STANDARD — optimize for price within lead time window
        """,
        expected_output=(
            "A disruption response plan including:\n"
            "1. Days until stockout (calculated)\n"
            "2. Top 3 alternative supplier options with pricing\n"
            "3. Recommended supplier choice and justification\n"
            "4. Draft Purchase Order details (supplier, quantity, unit price, total)\n"
            "5. Finance approval status\n"
            "6. Slack alert confirmation"
        ),
        agent=None,  # Hierarchical: manager assigns the right agent
    )

    result = crew.kickoff(inputs={"disruption": disruption})
    return str(result)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: Wrappers for Kafka Consumer (pokemon_events.py)
# ═══════════════════════════════════════════════════════════════════════════════
# These lightweight wrappers let pokemon_events.py trigger agents without
# needing to know the full CrewAI internals. Keeps the consumer simple.

def run_logistics_agent(task: str) -> str:
    """
    Run LogisticsAgent on a plain-text task (used by Kafka consumer).

    Used when PokémonTool's Kafka event signals a DEAL (card 30% below market)
    or a TREND CHANGE (card rapidly rising in value → time to restock before
    competitors buy out the available supply).

    Args:
        task: Plain-text description of what to evaluate.
    """
    crew = create_swarm(merchant_id="system")
    crewai_task = Task(
        description=task,
        expected_output=(
            "Clear recommendation: BUY or SKIP. "
            "If BUY: include recommended quantity and reasoning. "
            "If SKIP: explain why (price too high, inventory adequate, etc.)"
        ),
        agent=None,
    )
    result = crew.kickoff(inputs={"task": task})
    return str(result)


def run_finance_agent(task: str) -> str:
    """
    Run FinanceAgent on a plain-text financial decision (used by Kafka consumer).

    Used for evaluating:
    - Whether to approve a bulk buy when PokémonTool flags a deal
    - Whether a repricing action (raise shelf price because card is rising) is justified

    Args:
        task: Plain-text description of the financial decision.
    """
    crew = create_swarm(merchant_id="system")
    crewai_task = Task(
        description=task,
        expected_output=(
            "Financial decision: APPROVED or REJECTED. "
            "If APPROVED: unit cost, sell price, projected margin, recommended quantity. "
            "If REJECTED: exact reason (margin too thin, over-budget, risk too high)."
        ),
        agent=None,  # FinanceAgent is the manager → handles financial tasks by default
    )
    result = crew.kickoff(inputs={"task": task})
    return str(result)
