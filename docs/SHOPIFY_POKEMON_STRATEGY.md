# Shopify + Pokemon Strategy

## Core Idea

PokemonTool is the market-intelligence engine. Shopify is the commerce engine.

The product should help card sellers answer:

- What is this card worth right now?
- Did I buy it below market?
- What is my expected margin after fees?
- Should I list it, hold it, reprice it, or watch for more copies?
- Can I push this inventory to my Shopify store without manual duplicate entry?

## Product Loop

1. Seller adds owned cards to Pokemon inventory using PokeTCG search.
2. System stores exact card metadata, market price, purchase cost, quantity, and condition.
3. Seller sees cost basis, market value, and unrealized P&L.
4. Seller chooses cards to sell.
5. Shopify integration creates or updates Shopify products.
6. Pokemon market data keeps informing repricing and margin decisions.

## Why Shopify Exists Here

Shopify should not be the market intelligence source. PokemonTool is.

Shopify should handle:

- storefront,
- product listings,
- checkout,
- order history,
- customer data,
- vendor operations,
- subscriptions/billing if this becomes a Shopify app.

PokemonTool should handle:

- exact card lookup,
- market price,
- under-market alerts,
- inventory valuation,
- seller decision support,
- repricing recommendations.

## First Sellable Product

Start with a B2B SaaS for card sellers and local shops:

- market-backed inventory,
- watchlist alerts below market,
- position P&L,
- Shopify product export/sync,
- repricing suggestions,
- stale market data warnings.

Charge monthly. Do not start with a broad consumer app unless retention proves itself.

## First Shopify Integration Slice

Build a small, explicit workflow:

```text
Inventory card in PokemonTool
  -> click "Prepare Listing"
  -> choose price strategy
  -> create Shopify product draft
  -> seller reviews in Shopify
  -> publish when ready
```

Minimum fields to map:

- title: card name + set + number + condition
- description: rarity, set, number, condition, market reference, seller notes
- price: chosen listing price
- image: PokeTCG card image
- SKU: external card ID + condition
- inventory quantity: Pokemon inventory quantity
- tags: Pokemon, set name, rarity, condition

## Next Technical Work

1. Confirm existing Shopify OAuth/dev-store path in root `services/gateway`.
2. Add a Pokemon-to-Shopify integration boundary instead of mixing DBs directly.
3. Add a `listing_price` recommendation endpoint in Pokemon:
   - input: inventory item, condition, fees, desired margin
   - output: suggested Shopify price and explanation
4. Add a `Prepare Listing` action in Pokemon inventory.
5. Have NexusOS/Shopify gateway create a draft Shopify product.

## Guardrails

- Do not auto-publish products before the seller reviews them.
- Do not overwrite Shopify prices without an explicit seller action.
- Keep Pokemon market data freshness visible.
- Keep manual override fields because card condition and photos matter.
- Do not claim guaranteed profit. Show estimated margin.

