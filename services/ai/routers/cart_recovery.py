"""
NexusOS — Cart Abandonment Recovery Engine
==========================================

WHAT PROBLEM DOES THIS SOLVE?
Cart abandonment is the #1 conversion problem for Shopify stores.
Industry average: 70% of all shopping carts are abandoned before purchase.
That means for every 10 people who add something to their cart, 7 leave.

On a $40,000/month revenue store: if you could recover even 5% of abandoned carts,
that's an additional $4,000–$5,000+ per month. Automatically.

WHAT EXISTING TOOLS DO WRONG:
Most apps (Klaviyo, Omnisend) send the same generic email to everyone:
  "Hey! You left something behind! 🛒"

That's boring and they get ignored.

WHAT NEXUSOS DOES INSTEAD:

  1. KNOWS THE CONTEXT (using our data):
     - Why did they likely leave? (Price? Shipping cost? Just browsing?)
     - What's their purchase history? (New customer or VIP returning buyer?)
     - What's the product inventory situation? (Low stock = urgency is real)
     - Has the price changed? (If PokémonTool says card is RISING → even more urgent)

  2. HYPER-PERSONALIZED AI MESSAGE:
     Instead of a template, we write a UNIQUE email for each person using Claude.
     "Hi Alex! You checked out the Charizard Base Set — the same one you bought
      from us last year. Fun fact: it's up 15% this week according to market data.
      We only have 2 left. Here's a one-click link back to your cart."

  3. SMART TIMING:
     - First follow-up: 1 hour after abandonment (still warm)
     - Second: 24 hours later with a market insight (PokémonTool data)
     - Third: 72 hours WITH a small discount (only if they haven't bought)

  4. MARKET PRICE INTEGRATION:
     Since we have PokémonTool: if the abandoned card is RISING in value,
     the recovery email can truthfully say "This card has gone up $X since you
     looked at it. Prices may go higher." This is honest urgency, not fake scarcity.

FLOW:
  Shopify "checkouts/create" webhook → Gateway → Kafka "shopify.events"
    → This router detects it has NOT converted to an order after 1 hour
      → Generates personalized recovery email via Claude
        → Sends via Shopify Email / Klaviyo API / SendGrid
          → Tracks if it converted → updates campaign analytics
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from integrations.pokemon_client import pokemon_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cart-recovery", tags=["cart_recovery"])


# ─── Data Models ─────────────────────────────────────────────────────────────

class AbandonedCart(BaseModel):
    """
    Represents a shopping cart that was not completed.
    This comes from the Shopify "checkouts/create" webhook.

    SHOPIFY CHECKOUTS:
    In Shopify, a "checkout" is created the moment a customer enters
    their email on the checkout page. If they don't complete it
    within some time window, it's "abandoned."

    FIELD EXPLANATION:
      checkout_id       — Shopify's unique identifier for this checkout
      customer_email    — the email they entered (so we can contact them)
      customer_name     — their name (for personalization)
      customer_id       — Shopify customer ID (look up their history)
      total_price       — cart total if they had checked out
      items             — list of products they were about to buy
      abandoned_at      — when did they leave (used to time follow-ups)
      checkout_url      — direct link back to their cart (Shopify generates this)
    """
    checkout_id: str
    merchant_id: str
    customer_email: str
    customer_name: Optional[str] = None
    customer_id: Optional[str] = None
    total_price: float
    items: list[dict]      # e.g. [{"title": "Charizard", "quantity": 1, "price": 450.00}]
    abandoned_at: str      # ISO 8601 datetime string
    checkout_url: str      # direct link to resume checkout


class RecoveryEmailResult(BaseModel):
    """
    Result of generating a recovery email for an abandoned cart.

    FIELD EXPLANATION:
      subject    — the email subject line
      body_html  — full HTML email body (ready to send)
      body_text  — plain text version (for email clients that don't render HTML)
      send_at    — when to schedule this email (1h / 24h / 72h after abandonment)
      urgency_data — any real market data we included (price trend, inventory count)
    """
    checkout_id: str
    subject: str
    body_html: str
    body_text: str
    send_at: str
    urgency_data: Optional[dict] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/generate-email", response_model=RecoveryEmailResult)
async def generate_recovery_email(cart: AbandonedCart, email_number: int = 1) -> RecoveryEmailResult:
    """
    Generate a hyper-personalized cart abandonment recovery email.

    Args:
        cart: The abandoned cart data from Shopify
        email_number: Which email in the sequence (1, 2, or 3)
          - Email 1 (1h after): "Hey, you left something behind!"
          - Email 2 (24h after): Market insight email using PokémonTool data
          - Email 3 (72h after): Final attempt with a small discount

    HOW THE PERSONALIZATION WORKS:
    We build a context object with everything we know, then pass it to Claude
    with instructions to write a unique email (not a template fill-in).
    Claude knows: customer name, purchase history, specific products, market trends.

    WHY CLAUDE (NOT OLLAMA) FOR THIS?
    Recovery emails need to sound natural and human — not robotic.
    Ollama (free local model) would generate generic text.
    Claude 3.5 Sonnet is trained on excellent writing and produces
    emails that feel genuinely personalized. The $0.004 cost per email
    is worth it when recovering a $400+ cart.

    RETURNS:
    An email ready to send. The caller (Kafka consumer or cron job)
    is responsible for the actual sending via Shopify Email / SendGrid API.
    """
    from agents.router import HybridAIRouter

    router_instance = HybridAIRouter()
    llm = router_instance.get_llm("draft_customer_reply")  # → Claude 3.5 Sonnet

    # ── Step 1: Gather market context from PokémonTool ────────────────────
    # If any abandoned cart items are Pokemon cards, enrich with market data.
    market_insights = []
    urgency_data = {}

    for item in cart.items:
        item_title = item.get("title", "")

        # Heuristic: does this item name look like a Pokemon card?
        # We check for common Pokemon card identifiers in the title.
        if any(keyword in item_title.lower() for keyword in
               ["charizard", "pikachu", "mewtwo", "pokemon", "tcg", "base set",
                "shadowless", "first edition", "psa", "booster"]):
            # This looks like a Pokemon card! Fetch real market data.
            try:
                card_data = await pokemon_client.get_card_price(item_title)
                if card_data:
                    urgency_data[item_title] = {
                        "market_price": card_data.best_market_price,
                        "trend_label": card_data.trend_label,
                        "trending_score": card_data.trending_score,
                    }
                    if card_data.is_rising:
                        market_insights.append(
                            f"{item_title} is trending UP (score: {card_data.trending_score}/100). "
                            f"Market price has moved to ${card_data.best_market_price:.2f}."
                        )
                    elif card_data.is_falling:
                        market_insights.append(
                            f"{item_title} market is softening — our price may be more attractive soon."
                        )
            except Exception as e:
                logger.warning("[cart-recovery] PokémonTool unavailable for %s: %s", item_title, e)

    # ── Step 2: Build the items summary ───────────────────────────────────
    items_summary = "\n".join([
        f"  - {item.get('quantity', 1)}x {item.get('title', 'Unknown')} "
        f"(${float(item.get('price', 0)):.2f} each)"
        for item in cart.items
    ])

    customer_greeting = f"Hi {cart.customer_name.split()[0]}" if cart.customer_name else "Hi there"

    # ── Step 3: Craft the prompt based on email number in sequence ─────────
    if email_number == 1:
        # First email: friendly reminder, no pressure
        tone = "friendly and helpful, not pushy. Acknowledge they were browsing."
        include_discount = False
        subject_hint = "a friendly reminder they left something"

    elif email_number == 2:
        # Second email: add market insight (PokémonTool data makes this unique!)
        tone = "informative and engaging. Include the market trend data if available."
        include_discount = False
        subject_hint = "market intelligence about the items they viewed"

    else:
        # Third email: final attempt, include a small discount
        tone = "creating mild urgency. Offer a 5% discount as a final closing offer."
        include_discount = True
        subject_hint = "a time-limited 5% discount"

    market_context = ""
    if market_insights:
        market_context = (
            f"\n\nMarket intelligence from our price tracking system:\n"
            + "\n".join(market_insights)
        )

    prompt = f"""
Write a {tone} cart abandonment recovery email for an online Pokemon TCG card store.

Customer: {customer_greeting} ({cart.customer_email})
They abandoned their cart with these items:
{items_summary}
Total cart value: ${cart.total_price:.2f}
Direct checkout link: {cart.checkout_url}
{market_context}

Email number in sequence: {email_number} of 3
Email style: {tone}
Include discount: {include_discount} {"(5% off with code COMEBACK5)" if include_discount else ""}
Subject line hint: {subject_hint}

Write a unique, human-sounding email. NOT a generic template. 
Use specific details about what they were buying.
{"Include the market price trend data naturally in the email if it strengthens the case." if market_insights else ""}

Format your response as:
SUBJECT: [subject line here]
BODY: [email body here — plain text, no HTML tags]
""".strip()

    # ── Step 4: Generate the email with Claude ─────────────────────────────
    try:
        response = llm.invoke(prompt)
        raw_text = str(response)

        # Parse the structured response
        subject = "Your cart is waiting! 🛒"
        body_text = raw_text

        if "SUBJECT:" in raw_text and "BODY:" in raw_text:
            parts = raw_text.split("BODY:", 1)
            subject_part = parts[0].replace("SUBJECT:", "").strip()
            subject = subject_part.split("\n")[0].strip()
            body_text = parts[1].strip()

        # Convert plain text to simple HTML (preserve line breaks)
        body_html = "<html><body>"
        for paragraph in body_text.split("\n\n"):
            body_html += f"<p>{paragraph.replace(chr(10), '<br />')}</p>"
        body_html += "</body></html>"

    except Exception as e:
        logger.error("[cart-recovery] LLM failed to generate email: %s", e)
        # Fallback to a basic template if AI fails
        subject = f"You left something in your cart — ${cart.total_price:.2f} waiting"
        body_text = (
            f"{customer_greeting}!\n\n"
            f"You left {len(cart.items)} item(s) in your cart valued at ${cart.total_price:.2f}.\n\n"
            f"Click here to complete your order: {cart.checkout_url}\n\n"
            f"Thank you!"
        )
        body_html = f"<p>{body_text.replace(chr(10), '<br />')}</p>"

    # ── Step 5: Calculate send time based on email number ─────────────────
    # Email 1: send 1 hour after abandonment
    # Email 2: send 24 hours after abandonment
    # Email 3: send 72 hours after abandonment
    delays = {1: timedelta(hours=1), 2: timedelta(hours=24), 3: timedelta(hours=72)}
    abandoned_dt = datetime.fromisoformat(cart.abandoned_at.replace("Z", "+00:00"))
    send_at = (abandoned_dt + delays.get(email_number, timedelta(hours=1))).isoformat()

    logger.info("[cart-recovery] Generated email #%d for checkout %s (subject: %s)",
                email_number, cart.checkout_id, subject)

    return RecoveryEmailResult(
        checkout_id=cart.checkout_id,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        send_at=send_at,
        urgency_data=urgency_data if urgency_data else None,
    )
