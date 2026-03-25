"""
╔══════════════════════════════════════════════════════════════════════════╗
║  NexusOS — Fraud Detection & Chargeback Defense Engine                   ║
║  File: services/ai/routers/fraud.py                                      ║
╠══════════════════════════════════════════════════════════════════════════╣
║  WHY THIS IS ONE OF THE HIGHEST-VALUE FEATURES:                          ║
║                                                                          ║
║  THE REAL COST OF CHARGEBACKS TO A SHOPIFY MERCHANT:                    ║
║  ┌────────────────────────────────────────────────────────────────────┐  ║
║  │  Lost sale revenue:       $120.00                                  │  ║
║  │  Chargeback fee (Stripe): $15.00                                   │  ║
║  │  Lost product (shipped):  $85.00 (cost of goods)                  │  ║
║  │  Manual dispute work:     45 min of your time                     │  ║
║  │  TOTAL LOSS PER DISPUTE:  $220+ and almost an hour of work        │  ║
║  └────────────────────────────────────────────────────────────────────┘  ║
║  At 0.5% chargeback rate on $50K/month revenue:                         ║
║  → 5-10 disputes per month = $1,100-$2,200/month lost                  ║
║  → 4-8 hours per month in administrative work                           ║
║                                                                          ║
║  WHAT THIS MODULE DOES:                                                  ║
║                                                                          ║
║  FEATURE 1: Real-Time Order Risk Scoring (0-100)                        ║
║  Called immediately when a Shopify order.create webhook arrives.        ║
║  Checks 5 weighted risk factors, returns a score AND recommended action.║
║   Score  0-34 = LOW  → fulfill immediately                              ║
║   Score 35-69 = MED  → hold 2h, request ID verification                ║
║   Score 70-100 = HIGH → auto-cancel, refund, log for blacklist          ║
║                                                                          ║
║  FEATURE 2: Automated Chargeback Response                               ║
║  Called when a dispute.created webhook arrives.                         ║
║  GPT-4o drafts a professional evidenced dispute response in <1 minute.  ║
║  Industry win rate for automated evidence: ~35%.                        ║
║  Without response: 0% win rate (merchants don't have time to respond).  ║
║                                                                          ║
║  HOW IT FITS IN THE SYSTEM:                                             ║
║  Shopify webhook → Kafka → Python consumers → POST /fraud/score         ║
║  Stripe webhook  → Kafka → Python consumers → POST /fraud/dispute/respond║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# ── Standard library imports ───────────────────────────────────────────────────
import logging
import os
from typing import Optional

# ── Third-party imports ────────────────────────────────────────────────────────
import httpx  # async HTTP client — used for potential future external API calls

# FastAPI imports:
# APIRouter: a "mini-app" that groups related routes.
#   Instead of putting all routes in main.py, we organize by feature.
#   fraud.py has all fraud routes, cart_recovery.py has all cart routes, etc.
#   main.py includes all routers with `app.include_router(fraud_router)`.
# HTTPException: raises HTTP error responses with proper status codes.
#   raise HTTPException(status_code=500, detail="Error") → client gets {"detail": "Error"}
from fastapi import APIRouter, HTTPException

# pydantic BaseModel: data validation and parsing.
# When a POST /fraud/score request arrives with a JSON body, FastAPI uses Pydantic to:
#   1. Parse the JSON into a Python dict
#   2. Validate each field against the type annotations
#   3. Create an instance of the model with typed attributes
# If validation fails (wrong type, missing required field), FastAPI returns 422 automatically.
# EmailStr: a special Pydantic type that validates the value is a valid email format.
from pydantic import BaseModel, EmailStr

# Set up module-level logger
logger = logging.getLogger(__name__)

# Create the router for fraud-related endpoints.
# prefix="/fraud" means all routes in this router start with /fraud.
# So @router.post("/score") becomes POST /fraud/score.
# tags=["fraud"] groups these endpoints together in Swagger UI (/docs).
router = APIRouter(prefix="/fraud", tags=["fraud"])


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: Data Models (Pydantic)
# ═══════════════════════════════════════════════════════════════════════════════
#
# WHAT ARE PYDANTIC MODELS?
# In FastAPI, every request body and response is a Pydantic BaseModel.
# BaseModel provides:
#   - Automatic JSON parsing (JSON body → Python object)
#   - Type validation (string field sent as int → 422 error)
#   - Automatic documentation (Swagger UI shows all fields and types)
#   - .dict() method (convert back to dict for database storage)
#
# FIELD DECLARATION:
#   field_name: type         → required field, must be provided
#   field_name: type = value → optional field with default value
#   field_name: Optional[type] = None → explicitly optional, default None

class OrderRiskInput(BaseModel):
    """
    Input data for order risk scoring.

    Populated from the Shopify order.create webhook payload.
    The Go Gateway extracts these fields and calls POST /fraud/score.

    PYDANTIC VALIDATION EXAMPLES:
      - "total_price": "abc" → 422 error (not a float)
      - "order_id" missing → 422 error (required field)
      - "is_new_customer" missing → default value True is used
    """
    # Required fields (no default = must be present in request)
    order_id: str        # Shopify order ID, e.g., "5001234567890"
    merchant_id: str     # NexusOS merchant UUID (for multi-tenant data isolation)
    customer_email: str  # The email the customer used at checkout

    # Optional fields with defaults (these may not be available in all Shopify plans)
    ip_address: Optional[str] = None    # IP address at checkout (not always available)
    billing_country: Optional[str] = "US"    # Country code on the payment card
    shipping_country: Optional[str] = "US"   # Country we're shipping to

    total_price: float         # Order total in USD. e.g., 450.00
    is_new_customer: bool = True  # True if this is their first ever order

    # payment_attempts: how many times they tried to pay before succeeding.
    # Normal: 1 (first try works). Suspicious: 3+ (cycling through cards).
    payment_attempts: int = 1

    line_item_count: int = 1      # How many distinct products in the cart
    customer_order_count: int = 0 # How many previous orders this customer has placed


class RiskScoreResponse(BaseModel):
    """
    Output: the fraud risk assessment for an order.

    This response is returned to the caller (consumer/Go Gateway)
    which then decides what to do with the order based on `action`.

    FIELD MEANINGS:
      risk_score    0-100 fraud probability. 0=definitely safe, 100=definitely fraud.
      risk_level    Human-readable tier: "LOW" | "MEDIUM" | "HIGH"
      action        What NexusOS recommends: "approve" | "review" | "cancel"
      flags         List of specific risk signals detected. Each is a short string.
                    e.g., ["billing_shipping_country_mismatch", "new_customer_high_value_order"]
                    Used for merchant dashboard display and for building chargeback evidence.
      recommendation Plain English explanation. Shown to merchant in their dashboard.
    """
    order_id: str
    risk_score: int          # 0-100
    risk_level: str          # "LOW" | "MEDIUM" | "HIGH"
    action: str              # "approve" | "review" | "cancel"
    flags: list[str]         # detected risk signals
    recommendation: str      # human-readable explanation


class DisputeInput(BaseModel):
    """
    Input when a chargeback dispute is created by the customer.

    WHAT IS A CHARGEBACK?
    A customer goes to their bank and says "I didn't authorize this charge."
    The bank reverses the payment and charges the merchant a fee.
    The merchant has a limited time (7-20 days) to submit evidence to reverse it.

    Shopify sends a "disputes/created" webhook → we receive this model.
    We immediately generate and submit evidence before the deadline.

    DISPUTE REASONS (Stripe standard):
      "fraudulent"    → Customer claims the charge was unauthorized
      "not_received"  → Customer says they never got the item
      "duplicate"     → Customer says they were charged twice
      "product_not_as_described" → Item was different from description
      "credit_not_processed" → Refund was promised but not issued
      "unrecognized"  → Customer doesn't recognize the merchant name
    """
    dispute_id: str     # Stripe/Shopify dispute ID
    order_id: str       # Which order is being disputed
    merchant_id: str    # Which merchant (for data isolation)
    reason: str         # The dispute reason code (see above)
    amount: float       # How much is at stake (USD)
    due_by: str         # Deadline to respond (ISO 8601 datetime string)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: Order Risk Scoring Endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/score", response_model=RiskScoreResponse)
async def score_order_risk(order: OrderRiskInput) -> RiskScoreResponse:
    """
    Score an incoming Shopify order for fraud risk.

    FastAPI Decorator:
    @router.post("/score", response_model=RiskScoreResponse):
      - Registers this function as the handler for POST /fraud/score
      - FastAPI automatically validates the request body as OrderRiskInput
      - FastAPI validates the return value matches RiskScoreResponse
      - If return value has wrong types → 500 internal error

    HOW THE SCORING ALGORITHM WORKS:
    We use a WEIGHTED ADDITIVE scoring model:
      - Start at 0
      - Add points for each risk signal detected
      - Subtract points for trust signals (returning customer)
      - Clamp to 0-100
    
    DESIGN CHOICE: Why additive, not ML?
    An ML model would be more accurate BUT requires thousands of labeled fraud cases
    to train on — data we don't have at startup. The additive model:
    - Works immediately with zero training data
    - Is fully explainable (merchant can see exactly why order was flagged)
    - Can be tuned by merchants (adjust thresholds per business risk tolerance)
    - Accurate enough: even simple rules catch 60-70% of obvious fraud

    As fraud data accumulates in PostgreSQL, we can train an ML classifier
    and switch to that. The API interface doesn't change — just the scoring logic.

    Args:
        order: Validated OrderRiskInput from POST body

    Returns:
        RiskScoreResponse with score, level, action, flags, recommendation
    """
    # Initialize tracking variables
    flags = []     # list of detected risk signal names
    risk_score = 0  # starts at 0, we add/subtract based on signals

    # ── RISK FACTOR 1: Country Mismatch (weight: +30 pts) ─────────────────────
    # WHAT WE'RE DETECTING:
    # A UK-issued credit card being used to ship to a US address.
    # Legitimate international shoppers exist, but this pattern is also extremely
    # common in card fraud — stolen cards are often used to ship to the cardholder's
    # home country while the card itself is registered elsewhere.
    #
    # WHY +30 POINTS?
    # It's a strong fraud signal, but not definitive alone.
    # An expat living abroad with a home-country card is legitimate.
    # So 30 points puts a mismatch-only order at 30/100 = LOW risk (still OK).
    # But combined with other signals, it quickly escalates.
    if order.billing_country and order.shipping_country:
        # .upper() = convert to uppercase for case-insensitive comparison.
        # "us" vs "US" are the same country — .upper() normalizes both to "US".
        if order.billing_country.upper() != order.shipping_country.upper():
            risk_score += 30
            flags.append("billing_shipping_country_mismatch")

    # ── RISK FACTOR 2: New Customer + High Value Order (weight: +25 or +40 pts) ─
    # WHAT WE'RE DETECTING:
    # A brand new account immediately placing a large order.
    # Normal customers tend to start small and build up (trust-building behavior).
    # Fraudsters don't care about building a relationship — they want to maximize
    # their single purchase before the fraud is detected.
    #
    # TWO TIERS:
    # >$200: moderately suspicious → +25 pts
    # >$500: very suspicious (for a new customer) → +25 + 15 = +40 pts total
    if order.is_new_customer and order.total_price > 200:
        risk_score += 25
        flags.append("new_customer_high_value_order")

    if order.is_new_customer and order.total_price > 500:
        # Additional points on top of the base 25.
        # A new customer ordering $600+ in Pokemon cards is a major red flag.
        risk_score += 15
        flags.append("new_customer_very_high_value_order")

    # ── RISK FACTOR 3: Multiple Failed Payment Attempts (weight: +20 or +30 pts) ─
    # WHAT WE'RE DETECTING:
    # Carding: fraudsters test stolen credit cards by making purchases.
    # They might try cards #1, #2, #3 until one succeeds.
    # Normal customers rarely fail once. Failing 3+ times is highly suspicious.
    #
    # TIER 1 (3+ attempts): probably testing cards → +20 pts
    # TIER 2 (5+ attempts): definitely suspicious → +20+10 = +30 pts bonus
    if order.payment_attempts >= 3:
        risk_score += 20
        flags.append("multiple_payment_attempts")

    if order.payment_attempts >= 5:
        risk_score += 10  # additional 10 on top of the 20 already added
        flags.append("excessive_payment_attempts")

    # ── RISK FACTOR 4: Suspicious Email Domain (weight: +35 pts) ──────────────
    # WHAT WE'RE DETECTING:
    # Temporary/disposable email services create anonymous throwaway addresses.
    # Fraudsters use these so they don't reveal their real email.
    # Legitimate shoppers use real email addresses (they want order confirmation emails!)
    #
    # WHY THE HIGHEST WEIGHT (+35)?
    # A real customer NEVER uses a temp email for an online purchase they care about.
    # (They need the order confirmation, shipping updates, return instructions.)
    # Using a temp email is nearly always intentional anonymity → fraud intent.
    suspicious_domains = [
        "guerrillamail.com", "mailinator.com", "10minutemail.com",
        "throwam.com", "tempmail.com", "yopmail.com", "trashmail.com",
        "sharklasers.com", "guerrillamailblock.com", "grr.la",
        "spam4.me", "binkmail.com", "bob.email", "harakirimail.com",
    ]

    # Parse the domain from the email address.
    # "user@domain.com".split("@") → ["user", "domain.com"]
    # [-1] → takes the LAST element (the domain part)
    # Even if email has no "@", split("@") returns ["noemail"], [-1] = "noemail".
    # .lower() normalizes domain for case-insensitive comparison.
    email_domain = (
        order.customer_email.split("@")[-1].lower()
        if "@" in order.customer_email
        else ""
    )

    if email_domain in suspicious_domains:
        risk_score += 35
        flags.append("suspicious_email_domain")

    # ── TRUST SIGNAL: Returning Customer History (REDUCES risk) ───────────────
    # WHAT WE'RE DETECTING:
    # A customer with 10 successful previous orders is very unlikely to be a fraudster.
    # They've been a customer for a while — they have a real relationship with the store.
    # We SUBTRACT points to recognize trusted customers.
    #
    # WHY SUBTRACT?
    # Risk scoring should work in BOTH directions.
    # A returning customer who orders $600+ might still add 40 fraud points,
    # but subtracting 20 for being a trusted customer brings them to 20/100 = LOW.
    # That's correct behavior — long-term customers should be trusted more.
    if order.customer_order_count >= 5:
        risk_score -= 20
        flags.append("trusted_returning_customer")  # positive flag (reduces risk)
    elif order.customer_order_count >= 2:
        risk_score -= 10
        flags.append("known_returning_customer")

    # ── Normalize score: clamp to [0, 100] ───────────────────────────────────
    # Risk subtractions can make score negative (e.g., trusted customer with no flags).
    # Multiple risk signals can push above 100.
    # max(0, ...) prevents negative score. min(100, ...) prevents >100.
    # Chained: max(0, min(100, risk_score)) = clamp to [0, 100]
    risk_score = max(0, min(100, risk_score))

    # ── Determine Action Based on Score ──────────────────────────────────────
    # THREE-TIER SYSTEM:
    #   0-34  = LOW  → auto-approve (fulfill immediately)
    #   35-69 = MED  → hold and verify (delay fulfillment, send ID request)
    #   70-100 = HIGH → cancel (don't ship, refund immediately)
    if risk_score >= 70:
        risk_level = "HIGH"
        action = "cancel"
        recommendation = (
            f"Order #{order.order_id} has HIGH fraud risk (score: {risk_score}/100). "
            f"Risk signals detected: {', '.join(flags) if flags else 'none'}. "
            f"ACTION: Cancel this order and issue a full refund immediately. "
            f"Do NOT ship any items. Add customer email to fraud watchlist."
        )
    elif risk_score >= 35:
        risk_level = "MEDIUM"
        action = "review"
        recommendation = (
            f"Order #{order.order_id} has MEDIUM fraud risk (score: {risk_score}/100). "
            f"Signals detected: {', '.join(flags) if flags else 'none'}. "
            f"ACTION: Hold fulfillment for 2 hours. Send ID verification email to customer. "
            f"If no response in 24h: auto-approve and fulfill (most medium-risk orders are legitimate)."
        )
    else:
        risk_level = "LOW"
        action = "approve"
        recommendation = (
            f"Order #{order.order_id} appears legitimate (score: {risk_score}/100). "
            f"OK to fulfill immediately. "
            f"{'Trust signals: ' + ', '.join([f for f in flags if 'trusted' in f or 'returning' in f]) if any('trusted' in f or 'returning' in f for f in flags) else ''}"
        )

    # Log the result for monitoring/analytics
    logger.info(
        "[fraud] ✅ Order %s scored %d/100 → %s → action: %s",
        order.order_id, risk_score, risk_level, action
    )

    # Return a validated RiskScoreResponse.
    # FastAPI validates this against the response_model=RiskScoreResponse schema.
    # If any field is wrong type, FastAPI raises a 500 internal server error.
    return RiskScoreResponse(
        order_id=order.order_id,
        risk_score=risk_score,
        risk_level=risk_level,
        action=action,
        flags=flags,
        recommendation=recommendation,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: Automated Chargeback Response Endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/dispute/respond")
async def auto_respond_dispute(dispute: DisputeInput):
    """
    Automatically draft and submit evidence for a chargeback dispute.

    DO YOU KNOW WHAT THIS IS WORTH?
    The industry stat: merchants with automated dispute responses win 30-40% of cases.
    Merchants who don't respond (manually) win 0% (auto-loss by default).
    Most small merchants don't respond because writing a proper dispute response is:
      - Time-consuming (30-45 minutes of work)
      - Requires knowing the right evidence to submit
      - Easy to miss deadlines when you're busy running a store
    
    NexusOS responds in under 60 seconds — automatically — with properly
    formatted evidence documentation.

    HOW THIS WORKS:
    1. Receive the dispute details from Shopify webhook
    2. Look up the order's evidence (tracking, IP address, previous orders)
       [Currently: stubs. Production: query PostgreSQL + carrier API]
    3. Use GPT-4o to draft a professional, argument-structured dispute response
       (we use GPT-4o specifically because dispute responses need precise, persuasive writing)
    4. Return the response for merchant review in the Approvals dashboard
       [Currently: draft only. Production: submit directly to Stripe Disputes API]

    DISPUTE TYPES AND EVIDENCE:
    "not_received":    Tracking number + delivery confirmation + signature
    "fraudulent":      IP geolocation + previous orders + order confirmation email
    "duplicate":       Show orders have different items/dates
    "product_not_as_described": Show product listing matches what was shipped

    Args:
        dispute: DisputeInput with dispute_id, order_id, reason, amount, due_by

    Returns:
        Dict with status, response_preview, and action_required for merchant dashboard
    """
    # Import here (not at module top) to avoid circular imports.
    # The HybridAIRouter imports from other modules; importing at the top
    # could cause startup order issues.
    from agents.router import HybridAIRouter

    logger.info(
        "[fraud] 📋 Auto-responding to dispute %s for order %s "
        "(reason: %s, amount: $%.2f, deadline: %s)",
        dispute.dispute_id, dispute.order_id,
        dispute.reason, dispute.amount, dispute.due_by
    )

    # WHY GPT-4o FOR THIS TASK?
    # Dispute responses are high-stakes documents.
    # A poorly-written response that misses key points loses the case.
    # GPT-4o's "financial_analysis" tier in our router = the most capable model.
    # The $0.015 API cost is nothing compared to the $15+ chargeback fee
    # plus the sale amount we'd lose without a response.
    router_instance = HybridAIRouter()
    llm = router_instance.get_llm("financial_analysis")  # → GPT-4o

    # Build a different prompt for each dispute reason.
    # Each reason requires different evidence and argumentation strategy.
    # We give the LLM explicit instructions so it knows what to collect and write.
    if dispute.reason == "not_received":
        # Evidence strategy for "I never got my package" disputes:
        # Show proof of delivery (tracking + carrier confirmation).
        prompt = (
            f"You are a chargeback dispute specialist. "
            f"Write a professional, evidence-backed chargeback dispute response. "
            f"\n\nDispute Details:\n"
            f"  Order ID: {dispute.order_id}\n"
            f"  Dispute ID: {dispute.dispute_id}\n"
            f"  Reason: Customer claims package not received\n"
            f"  Amount: ${dispute.amount:.2f}\n"
            f"  Response Deadline: {dispute.due_by}\n"
            f"\nEvidence to Include:\n"
            f"  1. Shipping carrier name and tracking number\n"
            f"  2. Delivery confirmation date and time from carrier records\n"
            f"  3. Confirmed delivery address (matches customer's address)\n"
            f"  4. If available: signature confirmation or photo of delivery\n"
            f"  5. Order confirmation email sent to customer's email address\n"
            f"\nWrite the response in a professional, concise format suitable "
            f"for submission to Stripe/Visa. Lead with delivery confirmation facts. "
            f"Conclude by requesting the dispute be reversed."
        )
    elif dispute.reason == "fraudulent":
        # Evidence strategy for "I didn't make this charge" disputes:
        # Show proof that the real account holder placed the order.
        prompt = (
            f"You are a chargeback dispute specialist. "
            f"Write a professional dispute response for a 'fraudulent transaction' claim. "
            f"\n\nDispute Details:\n"
            f"  Order ID: {dispute.order_id}\n"
            f"  Dispute ID: {dispute.dispute_id}\n"
            f"  Reason: Customer claims transaction was fraudulent (not authorized)\n"
            f"  Amount: ${dispute.amount:.2f}\n"
            f"  Response Deadline: {dispute.due_by}\n"
            f"\nEvidence to Include:\n"
            f"  1. IP address at time of checkout with geolocation (matches billing address country)\n"
            f"  2. Customer's previous successful orders using the same account\n"
            f"  3. Order confirmation email sent and opened at customer's confirmed email\n"
            f"  4. Identical billing address used in previous orders\n"
            f"  5. Delivery tracking showing package received at customer's address\n"
            f"\nWrite a firm, factual response demonstrating the transaction was authorized. "
            f"Reference all evidence points clearly. Address the 'fraudulent' claim directly."
        )
    else:
        # Generic template for other dispute reasons
        prompt = (
            f"You are a chargeback dispute specialist. "
            f"Write a professional chargeback dispute response. "
            f"\n\nDispute Details:\n"
            f"  Order ID: {dispute.order_id}\n"
            f"  Dispute ID: {dispute.dispute_id}\n"
            f"  Reason: {dispute.reason}\n"
            f"  Amount: ${dispute.amount:.2f}\n"
            f"  Response Deadline: {dispute.due_by}\n"
            f"\nCollect all available evidence and write a comprehensive response. "
            f"Address the specific dispute reason with relevant evidence. "
            f"Conclude by requesting the dispute be reversed in our favor."
        )

    try:
        # llm.invoke(prompt) → sends the prompt to GPT-4o and returns a message object.
        # The message object has a .content attribute with the text response.
        response_content = llm.invoke(prompt)

        logger.info(
            "[fraud] ✅ Dispute response drafted for %s",
            dispute.dispute_id
        )

        # TODO: Submit to Stripe Dispute API (currently draft-only):
        # import stripe
        # stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        # stripe.Dispute.modify(
        #     dispute.dispute_id,
        #     evidence={
        #         "uncategorized_text": str(response_content.content),
        #         "shipping_documentation": tracking_info_pdf_url,
        #     }
        # )
        # After submission: create a notification record for the merchant dashboard.

        return {
            "status": "response_drafted",
            "dispute_id": dispute.dispute_id,
            "order_id": dispute.order_id,
            # Show first 500 chars in the API response as preview.
            # [:500] = Python slice notation: characters 0 through 499
            "response_preview": str(response_content.content)[:500] + "...",
            "action_required": (
                "Review the drafted response in the Approvals dashboard. "
                "Click Submit to send to Stripe, or edit before submitting."
            ),
            "deadline": dispute.due_by,
            "auto_submitted": False,  # True once we wire up the Stripe API
        }

    except Exception as e:
        # Log with full stack trace for debugging
        logger.error(
            "[fraud] ❌ Failed to generate dispute response for %s: %s",
            dispute.dispute_id, e, exc_info=True
        )
        # HTTPException with 500: tells FastAPI to return an HTTP 500 response.
        # The detail field becomes the response body: {"detail": "..."}.
        # The client (Go Gateway or merchant dashboard) sees the error message.
        raise HTTPException(
            status_code=500,
            detail=f"Dispute response generation failed: {e}"
        )
