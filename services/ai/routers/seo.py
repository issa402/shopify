"""
NexusOS — AI Product Description & SEO Engine
===============================================

WHAT PROBLEM DOES THIS SOLVE?
This is one of the most universally needed features for ANY Shopify store.

THE REAL COST OF BAD PRODUCT DESCRIPTIONS:
  - Generic descriptions: Google ranks you lower (thin content penalty)
  - Missing keywords: you're invisible in search → $0 organic traffic
  - No schema markup: products don't show star ratings/prices in Google results
  - Copy-paste from supplier: identical to 500 other stores → you compete on price only
  - Writing 500 product descriptions manually: ~250 hours of work

For a Pokemon TCG store with 500+ cards listed:
  - Each card needs a unique, SEO-optimized description
  - Each needs schema markup (Product schema for Google rich results)
  - Each needs proper title tags and meta descriptions
  
Doing this manually = impossible. NexusOS does it in bulk automatically.

WHAT THIS MODULE DOES:

  1. SINGLE PRODUCT DESCRIPTION
     Given a Shopify product (name, variant, condition, extra info),
     generate a unique, SEO-optimized description using Claude.
     Includes: keyword targeting, selling points, call-to-action.

  2. BULK GENERATION
     Process up to 50 products in one call.
     Uses asyncio.gather() to make parallel LLM calls — all 50 run at once.
     50 descriptions in ~30 seconds instead of ~25 minutes.

  3. SEO METADATA
     Generate title tag, meta description, and H1 for each product.
     These directly affect Google rankings.

  4. SCHEMA MARKUP
     Generate JSON-LD Product schema for Google rich results.
     Rich results = products show price, availability, ratings in Google search.
     Average 20-30% CTR improvement over non-rich results.

  5. POKÉMONTOOL INTEGRATION
     For Pokemon card products, enrich description with real market data:
     "This card's market value has risen 23% in the past month according
      to current TCGplayer pricing data."
     This adds trust signals and creates urgency organically. 

HOW AI AVOIDS GOOGLE PENALTIES:
  - Each description is UNIQUE (different prompt + card-specific details)
  - Never copy-paste between products
  - Human review step available before publishing
  - SEO guidelines baked into prompt (no keyword stuffing)
"""

import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from integrations.pokemon_client import pokemon_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/seo", tags=["SEO & Content"])


# ─── Data Models ─────────────────────────────────────────────────────────────

class ProductInput(BaseModel):
    """
    Everything we know about a product that helps generate a better description.

    The MORE fields you fill in, the BETTER the AI output.
    At minimum: product_name.
    Best results: all fields filled.

    FIELD EXPLANATION:
      product_name   — Shopify product title, e.g. "Charizard Holo 1st Edition Base Set PSA 9"
      product_type   — category, e.g. "Pokemon Card", "Booster Box", "Sealed Product"
      condition      — "PSA 9", "Near Mint", "Lightly Played", "Pack Fresh"
      extra_info     — any extra details: set name, year, rarity, special attributes
      target_keywords — SEO keywords to naturally include. e.g. ["charizard psa 9", "1999 base set"]
      brand_voice    — tone of writing: "professional", "enthusiastic", "collector-focused"
    """
    product_name: str
    product_type: Optional[str] = "Pokemon Card"
    condition: Optional[str] = None
    extra_info: Optional[str] = None
    target_keywords: Optional[list[str]] = None
    brand_voice: Optional[str] = "enthusiastic but professional"


class ProductSEOOutput(BaseModel):
    """
    Full SEO package for one product.

    All outputs here can be directly pasted into Shopify's admin:
      - description → Shopify product description field
      - title_tag → Shopify's SEO title field
      - meta_description → Shopify's meta description field
      - schema_markup → paste into theme's product.liquid <head> section

    FIELD EXPLANATION:
      description     — the main product description (HTML-safe text)
      title_tag       — browser tab title + Google search title (max 60 chars)
      meta_description — Google search snippet below title (max 160 chars)
      h1_heading      — the page's main heading (different from title_tag)
      schema_markup   — JSON-LD structured data for Google rich results
      market_insight  — if PokémonTool data was available, a market note
    """
    product_name: str
    description: str
    title_tag: str
    meta_description: str
    h1_heading: str
    schema_markup: str
    market_insight: Optional[str] = None


class BulkSEORequest(BaseModel):
    """
    Bulk request: up to 50 products processed in parallel.

    FIELD EXPLANATION:
      products    — list of product inputs (same as ProductInput above)
      store_name  — your store name (included in title tags and brand voice)
    """
    products: list[ProductInput]
    store_name: Optional[str] = "Our Store"


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=ProductSEOOutput)
async def generate_product_seo(product: ProductInput) -> ProductSEOOutput:
    """
    Generate a complete SEO package for ONE product.

    HOW TO CALL THIS:
      POST /seo/generate
      Body: {"product_name": "Charizard 1st Edition Base Set PSA 9", "condition": "PSA 9"}

    WHAT COMES BACK:
      A full SEO package with description, meta tags, and schema markup
      ready to paste into your Shopify admin.

    POKÉMONTOOL ENRICHMENT:
    If the product is a Pokemon card (we detect this from product_type or name),
    we automatically fetch live market price data from PokémonTool and include
    it in the description naturally:
      "Currently trading at $X on TCGplayer with a rising trend."
    This makes descriptions more accurate AND adds SEO-valuable fresh content.
    """
    from agents.router import HybridAIRouter

    ai_router = HybridAIRouter()
    llm = ai_router.get_llm("draft_customer_reply")  # Claude 3.5 Sonnet

    # ── Step 1: Fetch PokémonTool market data if applicable ───────────────
    market_insight = None
    market_context = ""

    is_pokemon_card = (
        product.product_type and "pokemon" in product.product_type.lower()
    ) or any(
        kw in product.product_name.lower()
        for kw in ["charizard", "pikachu", "mewtwo", "pokemon", "base set",
                   "shadowless", "psa", "bgs", "beckett", "tcg"]
    )

    if is_pokemon_card:
        try:
            card_data = await pokemon_client.get_card_price(product.product_name)
            if card_data and card_data.best_market_price > 0:
                trend_phrase = {
                    "RISING": f"up {abs(card_data.trending_score)}% in momentum",
                    "FALLING": "cooling in the market",
                    "STABLE": "holding steady in value",
                }.get(card_data.trend_label, "actively traded")

                market_insight = (
                    f"Current market price: ${card_data.best_market_price:.2f} "
                    f"(TCGplayer/eBay data, {trend_phrase})"
                )
                market_context = (
                    f"\n\nLIVE MARKET DATA (include naturally in description):\n"
                    f"  Current market value: ${card_data.best_market_price:.2f}\n"
                    f"  Price trend: {card_data.trend_label} (trending score: {card_data.trending_score}/100)\n"
                    f"  Include this data to add authenticity and urgency."
                )
        except Exception as e:
            logger.warning("[seo] PokémonTool unavailable for market data: %s", e)

    # ── Step 2: Build SEO generation prompt ───────────────────────────────
    keywords_str = ", ".join(product.target_keywords) if product.target_keywords else "none specified"
    condition_str = f"Condition: {product.condition}" if product.condition else ""
    extra_str = f"Additional info: {product.extra_info}" if product.extra_info else ""

    prompt = f"""
You are an expert e-commerce SEO copywriter specializing in Pokemon TCG collectibles.

Write a complete SEO package for this product listing:

PRODUCT: {product.product_name}
TYPE: {product.product_type or 'Pokemon Card'}
{condition_str}
{extra_str}
TARGET KEYWORDS: {keywords_str}
BRAND VOICE: {product.brand_voice}
{market_context}

PROVIDE ALL OF THE FOLLOWING (clearly labeled):

DESCRIPTION:
[Write 150-200 word unique product description. Naturally include target keywords.
 Mention card condition, collectibility, investment potential if applicable.
 Include market data if provided. End with a subtle call-to-action.
 NO keyword stuffing. Write naturally for humans first, search engines second.]

TITLE_TAG:
[Max 60 characters. Include primary keyword + brand signal. Format: "Product Name | Store Category"]

META_DESCRIPTION:
[Max 160 characters. Include main keyword, mention condition, include value proposition.
 Must make someone WANT to click from Google search results.]

H1_HEADING:
[The main page heading — similar to title but can be slightly longer. 1 line only.]

SCHEMA_MARKUP:
[JSON-LD Product schema for Google rich results. Include: name, description, 
 offers (price, availability, currency), brand. Use realistic placeholder for price if unknown.
 Format as valid JSON inside <script type="application/ld+json"> tags.]
""".strip()

    try:
        response = llm.invoke(prompt)
        raw = str(response)

        # Parse sections from the response
        def extract_section(text: str, section: str) -> str:
            """Extract content between section header and next header."""
            start = text.find(f"{section}:\n")
            if start == -1:
                start = text.find(f"{section}:")
            if start == -1:
                return ""
            start += len(section) + 1
            # Find the next section header or end of text
            next_sections = ["DESCRIPTION:", "TITLE_TAG:", "META_DESCRIPTION:",
                             "H1_HEADING:", "SCHEMA_MARKUP:"]
            end = len(text)
            for ns in next_sections:
                ns_pos = text.find(ns, start + 5)
                if ns_pos != -1 and ns_pos < end:
                    end = ns_pos
            return text[start:end].strip()

        description = extract_section(raw, "DESCRIPTION")
        title_tag = extract_section(raw, "TITLE_TAG")
        meta_description = extract_section(raw, "META_DESCRIPTION")
        h1_heading = extract_section(raw, "H1_HEADING")
        schema_markup = extract_section(raw, "SCHEMA_MARKUP")

        # Fallbacks if parsing fails
        if not description:
            description = f"Premium {product.product_name}. {condition_str}. {extra_str}"
        if not title_tag:
            title_tag = product.product_name[:60]
        if not meta_description:
            meta_description = f"Buy {product.product_name}. {condition_str}. Fast shipping."[:160]
        if not h1_heading:
            h1_heading = product.product_name
        if not schema_markup:
            schema_markup = json.dumps({
                "@context": "https://schema.org/",
                "@type": "Product",
                "name": product.product_name,
                "description": description[:200],
            })

        logger.info("[seo] Generated SEO package for: %s", product.product_name)

        return ProductSEOOutput(
            product_name=product.product_name,
            description=description,
            title_tag=title_tag[:60],
            meta_description=meta_description[:160],
            h1_heading=h1_heading,
            schema_markup=schema_markup,
            market_insight=market_insight,
        )

    except Exception as e:
        logger.error("[seo] SEO generation failed for %s: %s", product.product_name, e)
        # Return a basic fallback so the endpoint doesn't return 500
        return ProductSEOOutput(
            product_name=product.product_name,
            description=f"Shop {product.product_name}. {condition_str} {extra_str}".strip(),
            title_tag=product.product_name[:60],
            meta_description=f"Buy {product.product_name}. Fast shipping, great prices."[:160],
            h1_heading=product.product_name,
            schema_markup="{}",
            market_insight=market_insight,
        )


@router.post("/bulk-generate")
async def bulk_generate_seo(request: BulkSEORequest):
    """
    Generate SEO packages for multiple products IN PARALLEL.

    WHY PARALLEL?
    Generating one product description takes ~3 seconds (Claude API call).
    50 products sequentially = 50 × 3s = 150 seconds = 2.5 minutes.
    50 products in PARALLEL = still ~3 seconds (all run at the same time).

    This is asyncio.gather() — runs all coroutines concurrently.
    The Claude API rate limits at ~50 req/min on most plans, so max 50 per call.

    HOW TO CALL:
      POST /seo/bulk-generate
      Body: {
        "store_name": "Pokémon Paradise",
        "products": [
          {"product_name": "Charizard PSA 9"},
          {"product_name": "Blastoise Holo"},
          ...
        ]
      }

    RETURNS:
      List of SEO packages, one per product (same order as input).
    """
    if len(request.products) > 50:
        # Safety limit — 50 parallel Claude calls is a lot
        # Beyond 50, you'll hit API rate limits
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 products per bulk request. Split into batches."
        )

    logger.info("[seo] Starting bulk SEO generation for %d products", len(request.products))

    # asyncio.gather runs all coroutines concurrently.
    # return_exceptions=True means one failed product doesn't kill the others.
    # Each failed product returns an Exception object instead of a result.
    tasks = [generate_product_seo(product) for product in request.products]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert exceptions to error objects so the response is always a list
    output = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error("[seo] Bulk item %d failed: %s", i, result)
            output.append({
                "product_name": request.products[i].product_name,
                "error": str(result),
                "status": "failed",
            })
        else:
            output.append({**result.model_dump(), "status": "success"})

    success_count = sum(1 for r in output if r.get("status") == "success")
    logger.info("[seo] Bulk complete: %d/%d succeeded", success_count, len(request.products))

    return {
        "total": len(request.products),
        "succeeded": success_count,
        "failed": len(request.products) - success_count,
        "results": output,
    }
