"""
╔══════════════════════════════════════════════════════════════════════════╗
║  NexusOS — Shopify Admin API Client                                      ║
║  File: services/ai/lib/shopify_client.py                                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║  WHAT THIS FILE IS:                                                      ║
║  A clean async HTTP client that wraps the Shopify Admin REST API.        ║
║  Every CrewAI Tool that needs to touch Shopify (issue a refund,         ║
║  check inventory, update a product price) will import from here.        ║
║                                                                          ║
║  WHY A DEDICATED CLIENT?                                                 ║
║  Without this, every Tool would need to handle auth headers, error      ║
║  parsing, rate limiting, and base URL construction itself — that's      ║
║  500 lines of duplicated code. This module handles it once.             ║
║                                                                          ║
║  SHOPIFY ADMIN API BASICS:                                               ║
║  • Base URL: https://{shop_domain}/admin/api/2024-01/{resource}.json    ║
║  • Auth: X-Shopify-Access-Token header (stored in Postgres after OAuth) ║
║  • Rate limit: 2 requests/second (leaky bucket — bursts up to 40 rps)  ║
║  • Responses: always JSON. Errors in: {"errors": {...}}                 ║
║                                                                          ║
║  HOW AGENTS USE THIS:                                                    ║
║  The CrewAI tool calls:                                                  ║
║    client = ShopifyClient(shop_domain, access_token)                    ║
║    result = await client.create_refund(order_id, amount, reason)        ║
║                                                                          ║
║  HOW ACCESS TOKENS WORK:                                                 ║
║  When a merchant installs our app, Go gateway's OAuth handler           ║
║  stores their access_token in the merchants table. Before calling       ║
║  any Shopify API, we fetch it from Postgres by merchant_id.            ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os
import logging
import asyncio
from typing import Optional, Any
import httpx  # async HTTP client — same as requests but supports async/await

logger = logging.getLogger(__name__)

# The Shopify API version we're targeting.
# Pinned to a specific version so our code doesn't break when Shopify releases
# a new version with breaking changes. Update this intentionally, not by accident.
SHOPIFY_API_VERSION = "2024-01"


class ShopifyAPIError(Exception):
    """
    Custom exception for Shopify API failures.

    WHY CUSTOM EXCEPTIONS?
    Instead of checking `if response.status_code == 422` everywhere,
    callers can catch ShopifyAPIError and know it came from Shopify specifically.
    This separates Shopify errors from network errors from database errors.

    Attributes:
        status_code: HTTP status code from Shopify (e.g. 422, 429, 503)
        message: Human-readable error description
    """
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        # super().__init__ calls Exception.__init__ so Python sees this as a proper exception
        super().__init__(f"Shopify API error {status_code}: {message}")


class ShopifyClient:
    """
    Async Shopify Admin API client.

    WHAT IS AN ASYNC CLIENT?
    Normal (synchronous) code: you call an API → your program STOPS and waits
    for the response before doing anything else. Wasteful.

    Async code: you call an API → Python switches to doing other work while
    waiting → resumes when the response arrives. The event loop handles this.
    httpx.AsyncClient is the async version of the popular requests library.

    WHY ASYNC MATTERS HERE:
    A CrewAI agent might call CheckInventoryTool AND ShopifyRefundTool in the
    same reasoning step. If both are async, they can run concurrently (both
    HTTP requests in-flight at once). Sequential would take 2× as long.

    Usage:
        async with ShopifyClient(shop_domain, access_token) as client:
            data = await client.get_order("12345")
    OR (without context manager):
        client = ShopifyClient(shop_domain, access_token)
        data = await client.get_order("12345")
        await client.close()
    """

    def __init__(self, shop_domain: str, access_token: str):
        """
        Initialize the client for a specific merchant.

        Args:
            shop_domain: e.g. "my-pokemon-store.myshopify.com"
            access_token: OAuth access token from merchants table in Postgres
        """
        self.shop_domain = shop_domain
        self.access_token = access_token

        # Base URL for all API calls.
        # f-string builds: "https://my-pokemon-store.myshopify.com/admin/api/2024-01"
        self.base_url = f"https://{shop_domain}/admin/api/{SHOPIFY_API_VERSION}"

        # httpx.AsyncClient is the async HTTP session.
        # headers: sent with EVERY request from this client (no need to repeat per-call).
        # X-Shopify-Access-Token: how Shopify authenticates us.
        # Content-Type: tells Shopify we're sending JSON in POST bodies.
        # timeout: if Shopify doesn't respond in 15s, raise TimeoutError.
        self._client = httpx.AsyncClient(
            headers={
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=15.0,  # seconds — Shopify is usually fast but can be slow under load
        )

    async def close(self):
        """Close the underlying HTTP session. Always call this when done."""
        await self._client.aclose()

    # Context manager support: allows `async with ShopifyClient(...) as c:`
    # __aenter__ = called on entry to `async with` block
    # __aexit__  = called on exit (even if exception occurs) — ensures close() runs
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    async def _get(self, path: str) -> dict:
        """
        Internal GET request helper.

        Args:
            path: API path relative to base_url, e.g. "/orders/12345.json"

        Returns:
            Parsed JSON response as a Python dict.

        Raises:
            ShopifyAPIError: if Shopify returns a non-2xx status code.
        """
        url = f"{self.base_url}{path}"
        logger.debug("[shopify] GET %s", url)

        response = await self._client.get(url)

        # response.raise_for_status() raises httpx.HTTPStatusError for 4xx/5xx.
        # We catch it and re-raise as our custom ShopifyAPIError.
        if response.status_code >= 400:
            raise ShopifyAPIError(
                status_code=response.status_code,
                message=response.text[:500],  # truncate long error bodies
            )

        return response.json()  # parses JSON body → Python dict

    async def _post(self, path: str, data: dict) -> dict:
        """
        Internal POST request helper.

        Args:
            path: API path, e.g. "/orders/12345/refunds.json"
            data: dict that will be JSON-serialized as the request body

        Returns:
            Parsed JSON response as a Python dict.
        """
        url = f"{self.base_url}{path}"
        logger.debug("[shopify] POST %s payload=%s", url, data)

        response = await self._client.post(url, json=data)

        if response.status_code >= 400:
            raise ShopifyAPIError(
                status_code=response.status_code,
                message=response.text[:500],
            )

        return response.json()

    async def _put(self, path: str, data: dict) -> dict:
        """Internal PUT request helper for updating resources."""
        url = f"{self.base_url}{path}"
        response = await self._client.put(url, json=data)
        if response.status_code >= 400:
            raise ShopifyAPIError(response.status_code, response.text[:500])
        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # Orders
    # ──────────────────────────────────────────────────────────────────────────

    async def get_order(self, order_id: str) -> dict:
        """
        Fetch a single order from Shopify.

        Shopify response shape:
        {
          "order": {
            "id": 450789469,
            "order_number": 1001,
            "email": "customer@example.com",
            "total_price": "409.94",
            "financial_status": "paid",
            "line_items": [...],
            ...
          }
        }

        The actual order data is nested under the "order" key.
        We unwrap it with ["order"] so callers get the order dict directly.

        Args:
            order_id: Shopify order ID (NOT our internal UUID — Shopify's own bigint ID)

        Returns:
            Order dict from Shopify, or empty dict if not found.
        """
        try:
            data = await self._get(f"/orders/{order_id}.json")
            return data.get("order", {})
        except ShopifyAPIError as e:
            logger.error("[shopify] get_order %s failed: %s", order_id, e)
            raise

    async def get_recent_orders(self, limit: int = 50, status: str = "any") -> list[dict]:
        """
        Fetch recent orders for the merchant.

        Args:
            limit: Max orders to return (Shopify allows 1-250, default 50 is safe)
            status: "open" | "closed" | "cancelled" | "any"

        Returns:
            List of order dicts.
        """
        try:
            data = await self._get(f"/orders.json?limit={limit}&status={status}")
            return data.get("orders", [])
        except ShopifyAPIError as e:
            logger.error("[shopify] get_recent_orders failed: %s", e)
            return []

    async def create_refund(
        self,
        order_id: str,
        amount: float,
        reason: str,
        notify_customer: bool = True,
    ) -> dict:
        """
        Issue a refund for an order via Shopify Admin API.

        HOW SHOPIFY REFUNDS WORK:
        A refund in Shopify requires two things:
        1. refund_line_items: which specific line items are being refunded
        2. transactions: the actual money movement (from the payment gateway)

        For simplicity, we use the /calculate endpoint first to get the right
        refund amount (avoids over-refunding tax issues), then POST /refunds.json.

        The "transactions" array represents an actual money transfer back to the
        customer's payment method. "kind": "refund" means it's a refund (not a
        capture or sale).

        Args:
            order_id: Shopify order ID
            amount: Dollar amount to refund (e.g. 50.00)
            reason: Reason string shown in Shopify admin (e.g. "Item damaged in shipping")
            notify_customer: If True, Shopify sends the customer a refund email

        Returns:
            Shopify refund object with id, transactions, refund_line_items, etc.
        """
        payload = {
            "refund": {
                "notify": notify_customer,
                "note": reason,
                # transactions is the actual payment reversal
                # The refund amount comes from the original payment transactions
                "transactions": [
                    {
                        "kind": "refund",
                        "gateway": "shopify_payments",
                        "amount": str(amount),  # Shopify expects string, not float
                    }
                ],
                # shipping: False means we don't refund shipping costs
                # (the item failed, not the shipping service)
                "shipping": {"amount": "0.00"},
            }
        }

        logger.info(
            "[shopify] Creating refund: order=%s amount=$%.2f reason=%s",
            order_id, amount, reason
        )

        data = await self._post(f"/orders/{order_id}/refunds.json", payload)
        return data.get("refund", {})

    # ──────────────────────────────────────────────────────────────────────────
    # Inventory
    # ──────────────────────────────────────────────────────────────────────────

    async def get_inventory_level(self, inventory_item_id: int, location_id: int) -> dict:
        """
        Get current stock level for a specific inventory item at a location.

        HOW SHOPIFY INVENTORY WORKS:
        Products → Variants → InventoryItem (tracks stock globally)
        InventoryLevels = stock count per location (store, warehouse, 3PL)

        Most single-location stores have one location_id. Multi-location
        merchants have multiple (e.g. warehouse in NJ + store in NYC).

        Args:
            inventory_item_id: From product variant's inventory_item_id field
            location_id: From the merchant's locations list

        Returns:
            {"inventory_item_id": ..., "location_id": ..., "available": 145}
        """
        data = await self._get(
            f"/inventory_levels.json"
            f"?inventory_item_ids={inventory_item_id}&location_ids={location_id}"
        )
        levels = data.get("inventory_levels", [])
        return levels[0] if levels else {}

    async def adjust_inventory(
        self,
        inventory_item_id: int,
        location_id: int,
        adjustment: int,
    ) -> dict:
        """
        Adjust inventory level (positive = add stock, negative = remove stock).

        Args:
            inventory_item_id: The product variant's inventory item ID
            location_id: Which warehouse/location
            adjustment: +50 to receive 50 units, -10 to write off 10 units

        Returns:
            Updated inventory level object
        """
        payload = {
            "location_id": location_id,
            "inventory_item_id": inventory_item_id,
            "available_adjustment": adjustment,
        }
        data = await self._post("/inventory_levels/adjust.json", payload)
        return data.get("inventory_level", {})

    # ──────────────────────────────────────────────────────────────────────────
    # Products & Pricing
    # ──────────────────────────────────────────────────────────────────────────

    async def update_variant_price(
        self,
        product_id: str,
        variant_id: str,
        new_price: float,
        compare_at_price: Optional[float] = None,
    ) -> dict:
        """
        Update the price of a product variant on Shopify.

        Used by FinanceAgent when PokémonTool detects a card's market price has
        moved significantly — we reprice our Shopify listing automatically.

        HOW SHOPIFY PRICING WORKS:
        price = the actual selling price
        compare_at_price = the "original" price shown as crossed-out (for sale display)
        If compare_at_price > price → Shopify shows "Sale!" badge automatically.

        Args:
            product_id: Shopify product ID
            variant_id: The specific variant (e.g. PSA 9 vs raw copy of same card)
            new_price: New price in USD
            compare_at_price: Optional "was $X" price for sale badge display

        Returns:
            Updated variant object from Shopify
        """
        payload: dict = {
            "variant": {
                "id": variant_id,
                "price": f"{new_price:.2f}",  # Shopify wants "450.00" not 450.0
            }
        }

        if compare_at_price is not None:
            payload["variant"]["compare_at_price"] = f"{compare_at_price:.2f}"

        logger.info(
            "[shopify] Updating price: product=%s variant=%s price=$%.2f",
            product_id, variant_id, new_price
        )

        data = await self._put(f"/variants/{variant_id}.json", payload)
        return data.get("variant", {})

    async def get_product(self, product_id: str) -> dict:
        """
        Fetch a single product with all its variants.

        Returns:
            Product dict including variants[], title, handle, tags, etc.
        """
        data = await self._get(f"/products/{product_id}.json")
        return data.get("product", {})

    # ──────────────────────────────────────────────────────────────────────────
    # Customers
    # ──────────────────────────────────────────────────────────────────────────

    async def get_customer(self, customer_id: str) -> dict:
        """
        Fetch a customer profile including order history.

        Returns:
            Customer dict: email, first_name, last_name, orders_count, total_spent
        """
        data = await self._get(f"/customers/{customer_id}.json")
        return data.get("customer", {})

    async def get_customer_orders(self, customer_id: str, limit: int = 10) -> list[dict]:
        """
        Fetch a customer's order history.

        Args:
            customer_id: Shopify customer ID
            limit: Number of recent orders to return

        Returns:
            List of order dicts, most recent first
        """
        data = await self._get(
            f"/customers/{customer_id}/orders.json?limit={limit}&status=any"
        )
        return data.get("orders", [])

    # ──────────────────────────────────────────────────────────────────────────
    # Discount Codes (for Influencer Swarm feature)
    # ──────────────────────────────────────────────────────────────────────────

    async def create_discount_code(
        self,
        title: str,
        code: str,
        percentage: float,
        usage_limit: Optional[int] = None,
    ) -> dict:
        """
        Create a unique discount code for influencer tracking.

        HOW THIS WORKS:
        We create a "Price Rule" (the discount definition) then a "Discount Code"
        under it (the actual code customers type in). Multiple codes can share
        a price rule (e.g. all influencer codes = 15% off).

        Step 1 (this method): Create price rule
        Step 2 (separate call): Create code under that price rule

        Args:
            title: Internal name for the price rule (e.g. "INFLUENCER_JAKE_15")
            code: The actual code: "JAKE15" — what the customer types at checkout
            percentage: 15.0 = 15% off
            usage_limit: Max times this code can be used. None = unlimited.

        Returns:
            Created discount code object with id, code, created_at
        """
        # Step 1: Create the price rule
        price_rule_payload = {
            "price_rule": {
                "title": title,
                "target_type": "line_item",       # applies to products, not shipping
                "target_selection": "all",         # applies to ALL products in cart
                "allocation_method": "across",     # split discount across items
                "value_type": "percentage",
                "value": f"-{percentage}",         # Shopify needs NEGATIVE for discounts
                "customer_selection": "all",       # any customer can use it
                "starts_at": "2026-01-01T00:00:00Z",
                **({"usage_limit": usage_limit} if usage_limit else {}),
            }
        }

        rule_data = await self._post("/price_rules.json", price_rule_payload)
        rule_id = rule_data["price_rule"]["id"]

        # Step 2: Create the discount code under that price rule
        code_payload = {"discount_code": {"code": code}}
        code_data = await self._post(
            f"/price_rules/{rule_id}/discount_codes.json", code_payload
        )
        return code_data.get("discount_code", {})

    # ──────────────────────────────────────────────────────────────────────────
    # Metafields (for storing NexusOS AI data on Shopify resources)
    # ──────────────────────────────────────────────────────────────────────────

    async def set_product_metafield(
        self,
        product_id: str,
        namespace: str,
        key: str,
        value: str,
        type: str = "single_line_text_field",
    ) -> dict:
        """
        Store custom AI-generated data on a Shopify product.

        WHY METAFIELDS?
        Sometimes we want to store NexusOS-computed data directly on the
        Shopify product object so Shopify themes can read it without hitting
        our API. Examples:
          - nexusos.market_price = "452.00" (latest TCGplayer price)
          - nexusos.trend_label  = "RISING"
          - nexusos.seo_score    = "87"

        Metafields are Shopify's key-value extension system. They persist
        on the Shopify product forever (until we delete them).

        Args:
            product_id: Shopify product ID
            namespace: Grouping for our keys (use "nexusos" for all NexusOS data)
            key: Field name (e.g. "market_price", "trend_label")
            value: String value to store
            type: Shopify metafield type — "single_line_text_field" for short strings

        Returns:
            Created/updated metafield object
        """
        payload = {
            "metafield": {
                "owner_id": int(product_id),
                "owner_resource": "product",
                "namespace": namespace,
                "key": key,
                "value": value,
                "type": type,
            }
        }
        data = await self._post("/metafields.json", payload)
        return data.get("metafield", {})


# ─── Token Fetch Helper ───────────────────────────────────────────────────────

async def get_shopify_client_for_merchant(merchant_id: str) -> Optional[ShopifyClient]:
    """
    Build a ShopifyClient for a specific merchant by fetching their
    credentials from PostgreSQL.

    WHY THIS FUNCTION EXISTS:
    The ShopifyClient needs shop_domain + access_token.
    Those live in the Postgres `merchants` table (stored during OAuth).
    This function is the bridge between merchant_id (what agents know)
    and the credentials (what Shopify requires).

    HOW POSTGRES ACCESS WORKS FROM PYTHON:
    We use asyncpg — the async PostgreSQL driver.
    pool.fetchrow() executes a SQL query and returns one row as a dict-like object.
    If no merchant is found, fetchrow() returns None.

    Args:
        merchant_id: Our internal UUID from the merchants table

    Returns:
        ShopifyClient ready to use, or None if merchant not in DB.
    """
    import asyncpg  # async PostgreSQL driver for Python

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("[shopify] DATABASE_URL not set — cannot fetch merchant credentials")
        return None

    try:
        # asyncpg.connect() opens a single DB connection.
        # For production, prefer a connection pool (asyncpg.create_pool()).
        # Single connection is fine here since this is called once per tool invocation.
        conn = await asyncpg.connect(database_url)

        # Parameterized query using $1 placeholder.
        # NEVER use f-strings for SQL — that's SQL injection risk.
        # asyncpg substitutes $1 safely (as a bound parameter, not string concatenation).
        row = await conn.fetchrow(
            "SELECT shop_domain, access_token FROM merchants WHERE id = $1 AND is_active = TRUE",
            merchant_id,
        )
        await conn.close()  # always close connections when done

        if row is None:
            logger.warning("[shopify] Merchant %s not found in DB", merchant_id)
            return None

        # row["shop_domain"] and row["access_token"] are the column values
        return ShopifyClient(
            shop_domain=row["shop_domain"],
            access_token=row["access_token"],
        )

    except Exception as e:
        logger.error("[shopify] Failed to fetch merchant credentials: %s", e)
        return None
