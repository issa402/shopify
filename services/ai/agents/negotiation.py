"""
NexusOS A2A Negotiation Swarm

Handles automated price negotiation with customer AI agents.
Invoked when a request to POST /api/v1/agent/negotiate is forwarded
from the Go gateway to this Python service.

Flow:
  1. Parse ProductQuery from incoming agent
  2. LogisticsAgent checks inventory availability
  3. FinanceAgent calculates max allowable discount
  4. Return Offer or CounterOffer
  5. If bulk B2B: generate Contract
"""
from pydantic import BaseModel
from typing import Optional
from agents.router import HybridAIRouter
import uuid
import datetime


# ─── Schema (mirrors Go types) ─────────────────────────────────────────────────

class QueryConstraints(BaseModel):
    max_price_usd: float = 0.0
    required_tags: list[str] = []
    max_shipping_days: int = 7
    preferred_currency: str = "USD"
    b2b: bool = False


class ProductQuery(BaseModel):
    agent_id: str
    agent_type: str = "unknown"
    session_id: str = ""
    query: str
    constraints: QueryConstraints = QueryConstraints()
    quantity: int = 1


class ProductMatch(BaseModel):
    product_id: str
    title: str
    price_usd: float
    discount_pct: float = 0.0
    final_price_usd: float
    inventory_available: int
    estimated_shipping_days: int


class Offer(BaseModel):
    offer_id: str
    session_id: str
    products: list[ProductMatch]
    expires_at: str
    negotiation_url: Optional[str] = None
    protocol: str = "nexusos-a2a/1.0"
    message: Optional[str] = None


class Contract(BaseModel):
    contract_id: str
    session_id: str
    offer_id: str
    agent_id: str
    products: list[ProductMatch]
    total_usd: float
    status: str  # accepted | pending_payment
    created_at: str
    payment_url: Optional[str] = None


# ─── Negotiation Engine ───────────────────────────────────────────────────────

class NegotiationEngine:
    """
    Orchestrates the A2A negotiation process.
    Uses FinanceAgent logic to determine maximum discount.
    """

    def __init__(self):
        self.router = HybridAIRouter()
        self.max_discount_pct = 25.0  # Never exceed 25% discount
        self.min_margin_pct = 15.0    # Never sell below 15% margin

    async def process_query(self, query: ProductQuery, merchant_id: str) -> Offer:
        """
        Process an A2A ProductQuery and return an Offer with REAL market pricing.

        HOW THIS WORKS NOW (vs the old stub approach):
          Old way: We always said the price was $99.00 (hardcoded fake price).
          New way: We call PokémonTool's actual REST API to get the real
                   TCGplayer market price before building the offer.
                   We also look at the trend (RISING/FALLING) to adjust discounts.

        TREND-AWARE DISCOUNTING:
          - If the card is RISING in price → reduce discount (market going up,
            no need to give away value. The card will be worth MORE tomorrow).
          - If the card is FALLING → increase discount slightly (move inventory
            before the price drops further).
          - If STABLE → apply standard discount logic.

        FALLBACK:
          If PokémonTool is down or doesn't have this card, we fall back to
          a $99.00 placeholder price. The negotiation still works, just without
          real market data. This is "fail open" — we'd rather give a possibly
          wrong price than fail the whole negotiation with a 500 error.
        """
        import asyncio
        from integrations.pokemon_client import pokemon_client

        # 1. Use Ollama (free, local) just to classify the intent type.
        #    This is cheap — we don't need GPT-4o just to figure out if someone
        #    is buying running shoes vs. bulk corporate equipment.
        _llm = self.router.get_llm("route_intent")

        # 2. Fetch REAL market price from PokémonTool.
        #    We do this before calculating discounts because the discount
        #    logic depends on the trend that PokémonTool computed.
        market_price = 99.00           # fallback price if PokémonTool unavailable
        trend_label = "STABLE"         # fallback trend
        trending_score = 0             # fallback score (neutral)

        try:
            # Call PokémonTool's existing /api/cards/search endpoint.
            # This is an async HTTP GET — it takes ~50ms on average.
            card_data = await pokemon_client.get_card_price(query.query)

            if card_data is not None:
                # We got real price data! Use the TCGplayer price as our baseline
                # (TCGplayer is the most reliable Pokemon card price reference).
                market_price = card_data.best_market_price  # prefers TCGplayer > eBay
                trend_label = card_data.trend_label          # "RISING", "STABLE", "FALLING"
                trending_score = card_data.trending_score    # -100 to 100

        except Exception as e:
            # If anything goes wrong calling PokémonTool (timeout, connection error, etc.)
            # we log it but continue with the fallback price.
            # We never want a PokémonTool outage to break A2A negotiations.
            print(f"[negotiation] ⚠️ PokémonTool unavailable ({e}), using fallback price ${market_price:.2f}")

        # 3. Calculate the discount using trend-aware logic.
        #    Base discount comes from B2B quantity rules.
        #    Then we adjust based on PokémonTool's trend signal.
        discount = self._calculate_discount_with_trend(query, trend_label, trending_score)

        # 4. Build the list of matched products for the Offer.
        #    In production: query Qdrant with semantic search to find actual Shopify products.
        #    For now: use the market price we fetched + the trend-adjusted discount.
        products = [
            ProductMatch(
                product_id=f"prod_{str(uuid.uuid4())[:8]}",
                title=f"{query.query}",
                price_usd=market_price,                                    # real market price!
                discount_pct=discount,
                final_price_usd=round(market_price * (1 - discount / 100), 2),
                inventory_available=250,                                   # TODO: query Postgres
                estimated_shipping_days=2,
            )
        ]

        # 5. Build and return the Offer.
        offer_id = str(uuid.uuid4())
        # Offers expire in 15 minutes — long enough for the buyer agent to
        # process and accept, short enough that we're not locked into a price
        # while the market moves.
        expires_at = (datetime.datetime.utcnow() + datetime.timedelta(minutes=15)).isoformat() + "Z"

        message = None
        if query.constraints.b2b and query.quantity >= 50:
            message = (
                f"Bulk pricing applied: {discount:.0f}% discount for {query.quantity}+ units. "
                f"Market price anchored to TCGplayer (${market_price:.2f}). "
                f"Trend: {trend_label}. "
                f"A Contract can be generated on offer acceptance."
            )
        elif trend_label == "RISING":
            message = f"Note: Market is trending UP (+{trending_score} score). Prices may be higher tomorrow."
        elif trend_label == "FALLING":
            message = f"Note: Market is trending DOWN ({trending_score} score). Act soon for best opportunity."

        return Offer(
            offer_id=offer_id,
            session_id=query.session_id,
            products=products,
            expires_at=expires_at,
            negotiation_url=f"/api/v1/agent/negotiate?session={query.session_id}",
            message=message,
        )


    def generate_contract(self, offer: Offer, query: ProductQuery) -> Contract:
        """Convert an accepted Offer into a legally-binding Contract."""
        total = sum(p.final_price_usd * query.quantity for p in offer.products)

        return Contract(
            contract_id=str(uuid.uuid4()),
            session_id=offer.session_id,
            offer_id=offer.offer_id,
            agent_id=query.agent_id,
            products=offer.products,
            total_usd=round(total, 2),
            status="pending_payment",
            created_at=datetime.datetime.utcnow().isoformat() + "Z",
            payment_url=f"/checkout/agent/{offer.offer_id}",
        )

    def _search_products(self, query: ProductQuery) -> list[dict]:
        """Stub product search. Production: semantic search via Qdrant + Shopify API."""
        return [
            {
                "id": f"prod_{str(uuid.uuid4())[:8]}",
                "title": f"Product matching: {query.query}",
                "price": 99.00,
                "stock": 250,
            }
        ]

    def _calculate_discount(self, query: "ProductQuery") -> float:
        """
        Original discount logic — B2B quantity tiers only. No trend adjustment.
        FinanceAgent rules:
          - Not B2B → 0% (retail price, no discount)
          - B2B + fewer than 10 units → 5%
          - B2B + 10–49 units → 10%
          - B2B + 50+ units → 20%
          - Never exceed max_discount_pct (default: 25%)
        """
        if not query.constraints.b2b:
            return 0.0

        if query.quantity >= 50:
            discount = 20.0
        elif query.quantity >= 10:
            discount = 10.0
        else:
            discount = 5.0

        return min(discount, self.max_discount_pct)

    def _calculate_discount_with_trend(
        self, query: "ProductQuery", trend_label: str, trending_score: int
    ) -> float:
        """
        Trend-aware discount calculation using PokémonTool's market signal.

        This is an improvement over _calculate_discount: instead of applying
        the same discount regardless of market conditions, we adjust based on
        whether the card's price is trending up or down.

        WHY THIS MATTERS:
          Imagine Charizard's price jumped 15% this week (trending_score = 75).
          Giving a 20% B2B bulk discount on a RISING card means we're selling
          below tomorrow's market price — bad for margins.
          Conversely, if the price is FALLING we should move inventory faster
          by offering a slightly bigger discount.

        TREND ADJUSTMENT RULES:
          - RISING  (score > 50):  Cut discount by 50% (e.g., 20% → 10%)
          - RISING  (score 20–50): Cut discount by 25% (e.g., 20% → 15%)
          - FALLING (score < -50): Add 5% extra discount to move inventory fast
          - FALLING (score -20–50): Add 2% extra discount
          - STABLE: No adjustment, use base discount

        The final discount is always capped at max_discount_pct (25%).
        """
        # Get the base discount from quantity/B2B tier rules
        base_discount = self._calculate_discount(query)

        # Apply trend adjustment
        if trend_label == "RISING":
            if trending_score > 50:
                # Strongly rising market — cut our discount significantly.
                # We don't need to offer good deals when the card is appreciating.
                adjusted = base_discount * 0.5  # halve the discount
            elif trending_score > 20:
                # Moderately rising — reduce discount somewhat
                adjusted = base_discount * 0.75
            else:
                # Mildly rising — minimal adjustment
                adjusted = base_discount

        elif trend_label == "FALLING":
            if trending_score < -50:
                # Strongly falling — add 5% extra to move inventory now
                # before the price drops further.
                adjusted = base_discount + 5.0
            elif trending_score < -20:
                # Moderately falling — add 2% extra
                adjusted = base_discount + 2.0
            else:
                adjusted = base_discount

        else:
            # STABLE trend — no adjustment, standard rules apply
            adjusted = base_discount

        # Always cap at our maximum discount regardless of trend adjustments.
        # We never discount more than max_discount_pct, even for heavily falling cards.
        return min(adjusted, self.max_discount_pct)

