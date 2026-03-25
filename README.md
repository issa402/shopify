# NexusOS — AI Operating System for Shopify Stores

> **NexusOS is not a dashboard. It is not a chatbot.**  
> It is an autonomous AI operations layer that runs your Shopify store 24/7 — resolving support tickets, preventing fraud, recovering abandoned carts, forecasting inventory, negotiating B2B deals using real market data, and writing SEO product descriptions — while asking you to approve anything that costs real money.

Built with **Go (API Gateway) + Python (AI Agents) + React (Dashboard)**.  
Integrates with **PokémonTool** for live TCG card market intelligence.

---

## What It Solves (And What It Earns You)

| Problem | What NexusOS Does | Revenue Impact |
|---------|------------------|---------------|
| Support tickets pile up (2-4 hrs/day) | SupportAgent resolves autonomously using RAG over past tickets | ~$3K–6K/month in time savings |
| 70% of carts abandoned | CartRecoveryAgent sends unique Claude-written emails with live card market data | +$2K–5K/month recovered |
| Chargebacks eat margins | FraudAgent scores every order in <2s + auto-builds chargeback evidence in 10 min | Save 30–40% of dispute value |
| Inventory stockouts / overstock | Prophet ML forecasting + LogisticsAgent drafts purchase orders | Eliminate $500–2K/month in lost sales |
| Shopify pricing lags market | PokémonTool pushes price trends → FinanceAgent adjusts listings automatically | Never leave money on the table |
| B2B wholesale buyers need quotes | A2A NegotiationEngine quotes with real TCGplayer/eBay market prices | Close deals while you sleep |
| 500 product descriptions = 250 hours | AI SEO Engine generates unique descriptions + JSON-LD schema markup in bulk | 20-30% higher Google CTR |

---

## Architecture

```
Shopify (webhooks) ──► Go Gateway :8080 ──► Kafka ──► Python AI :8000
                              ▲                               │
                              │                               ▼
PokémonTool :3001 ────────────┘              3 CrewAI Agents (Support/Logistics/Finance)
(card prices, deals, trends)                 5 Routers (Fraud/Cart/SEO/Negotiate/Inventory)
                                             1 Kafka Consumer (Pokemon events)
```

**Infrastructure (all via Docker Compose):**  
PostgreSQL + pgvector · Redis · Qdrant · Kafka · Ollama (local LLM) · Temporal

---

## Quick Start (Ubuntu Linux)

```bash
# 1. Install prerequisites
sudo apt-get install -y docker.io docker-compose-plugin
# Install Go 1.22, Python 3.11, Node 20 — see NEXUSOS_MASTER_DOC.md for commands

# 2. Copy and fill environment files
cp .env.example .env          # fill: SHOPIFY_*, ANTHROPIC_API_KEY, OPENAI_API_KEY
cd Pokemon && cp .env.example .env  # fill: NEXUSOS_GATEWAY_URL, INTERNAL_SECRET

# 3. Start Docker infrastructure
docker compose up -d          # NexusOS: Postgres, Redis, Kafka, Qdrant, Ollama...
cd Pokemon && docker compose up -d   # PokémonTool: its own Postgres, Redis, RabbitMQ

# 4. Start services (3 terminals)
cd services/gateway && go run ./main.go                  # :8080
cd services/ai && pip install -r requirements.txt && \
  python -m uvicorn main:app --port 8000 --reload        # :8000
cd apps/web && npm install && npm run dev                # :3000

# 5. Start PokémonTool Go server
cd Pokemon/server && go run ./main.go                    # :3001

# 6. Verify
curl http://localhost:8080/health   # Gateway
curl http://localhost:8000/health   # AI Service
curl http://localhost:3001/health   # PokémonTool

# 7. Open
# Dashboard: http://localhost:3000
# AI API docs: http://localhost:8000/docs
# Temporal UI: http://localhost:8088
```

---

## Feature Set

### 🎫 AI Support Agent
SupportAgent uses RAG (semantic search over past resolved tickets) to find similar past resolutions, checks Shopify order status, and drafts or sends a resolution. Escalates to you only for complex edge cases. Uses Claude 3.5 Sonnet.

### 📦 Inventory Forecasting
Facebook Prophet ML model predicts 30-day demand from 90 days of sales history. LogisticsAgent calculates reorder points, then creates a draft Purchase Order you approve with one click.

### 🛡️ Fraud Detection + Chargeback Defense
Every order scored 0-100 using weighted risk factors (country mismatch, new customer + high value, temp email, multiple payment attempts). Score 71+: auto-cancel. Chargeback disputes: auto-build evidence package and draft response within 10 minutes — you'd otherwise lose by not responding.

### ✉️ Cart Abandonment Recovery
3-email sequence. Email 1 (1h): friendly reminder. Email 2 (24h): if it's a Pokemon card, includes LIVE market data from PokémonTool ("That Charizard is up 15% this week"). Email 3 (72h): 5% discount code. Each written uniquely by Claude — not a template.

### 🤝 A2A Commerce — B2B Negotiation
Buyer AI agents POST structured ProductQuery → NegotiationEngine fetches real current price from PokémonTool → applies trend-aware discount (RISING card = smaller discount) → returns Offer → generates Contract on acceptance. Handles wholesale B2B autonomously.

### 📈 Market-Driven Repricing (PokémonTool Integration)
When PokémonTool's analytics engine detects a card trending significantly, it pushes the event to NexusOS via HTTP bridge → Kafka → Python consumer → FinanceAgent adjusts our Shopify listing price. All changes >$50 require your approval.

### 🔍 AI SEO Engine
Send a product name → get back: unique description, title tag (60 char), meta description (160 char), H1, and JSON-LD schema markup for Google rich results. Bulk mode: 50 products in parallel in ~30 seconds. Pokemon cards get enriched with live PokémonTool pricing data.

---

## Security

| Layer | How |
|-------|-----|
| Shopify webhooks | HMAC-SHA256 verification (constant-time comparison) |
| Service-to-service (PokémonTool ↔ NexusOS) | `X-Internal-Secret` shared header |
| Multi-tenant data isolation | PostgreSQL Row-Level Security on all tables |
| API auth | JWT Bearer tokens + Role-Based Access Control |
| Human-in-the-Loop | All costly AI actions → `approval_queue` → you click approve/reject |
| Webhook deduplication | Redis idempotency keys (24h TTL) |

---

## Environment Variables

| Variable | Where | What it does |
|----------|-------|-------------|
| `SHOPIFY_CLIENT_ID` | `.env` | Your Shopify app's client ID |
| `SHOPIFY_CLIENT_SECRET` | `.env` | Your Shopify app's secret |
| `SHOPIFY_WEBHOOK_SECRET` | `.env` | For HMAC verification |
| `ANTHROPIC_API_KEY` | `.env` | Claude 3.5 Sonnet |
| `OPENAI_API_KEY` | `.env` | GPT-4o for financial/risk tasks |
| `DATABASE_URL` | `.env` | PostgreSQL connection string |
| `REDIS_URL` | `.env` | Redis connection |
| `KAFKA_BROKERS` | `.env` | Kafka broker address |
| `JWT_SECRET` | `.env` | Sign/verify JWTs |
| `INTERNAL_SECRET` | `.env` + `Pokemon/.env` | Must be IDENTICAL in both — authenticates the integration bridge |
| `POKEMONTOOL_API_URL` | `.env` | NexusOS pulls prices from PokémonTool here |
| `NEXUSOS_GATEWAY_URL` | `Pokemon/.env` | PokémonTool pushes events to NexusOS here |

---

## Full Documentation

See [NEXUSOS_MASTER_DOC.md](./NEXUSOS_MASTER_DOC.md) for:
- Every file in both projects explained
- All data flows traced step-by-step
- Complete Ubuntu Linux setup with terminal commands
- Full API reference table
- Integration readiness checklist

---

## Project Structure

```
shopify/
├── services/
│   ├── gateway/           # Go API Gateway
│   │   ├── main.go        # Entry point
│   │   └── internal/
│   │       ├── auth/      # Shopify OAuth
│   │       ├── webhook/   # HMAC verification + Kafka publish
│   │       ├── pokemon/   # PokémonTool client + inbound handler
│   │       ├── a2a/       # B2B negotiation endpoint
│   │       ├── kafka/     # Kafka producer
│   │       ├── middleware/ # JWT, RBAC, CORS
│   │       ├── db/        # PostgreSQL pool + migrations + RLS
│   │       └── mcp/       # MCP tool hub
│   └── ai/                # Python AI Service
│       ├── main.py        # FastAPI + all routers registered
│       ├── agents/        # CrewAI agents + HybridAIRouter
│       ├── consumers/     # Kafka consumers (PokémonTool events)
│       ├── integrations/  # PokémonTool client
│       ├── rag/           # Qdrant RAG pipeline
│       ├── inventory/     # Prophet forecasting
│       └── routers/       # HTTP endpoints (fraud, seo, cart-recovery...)
├── apps/web/              # React merchant dashboard
├── Pokemon/               # PokémonTool microservice (separate project)
│   ├── server/            # Go API + nexusos/bridge.go (integration)
│   └── services/          # Python scraping + analytics
├── docker-compose.yml     # All infrastructure services
├── Makefile               # Developer shortcuts
└── .env.example           # All environment variable templates
```

---

*NexusOS — Built for Pokemon TCG store owners who want to run a 7-figure business without a 10-person operations team.*
