"""
╔══════════════════════════════════════════════════════════════════════════╗
║  NexusOS AI Service — FastAPI Application Entry Point                    ║
║  File: services/ai/main.py                                               ║
╠══════════════════════════════════════════════════════════════════════════╣
║  WHAT IS THIS FILE?                                                      ║
║  The ROOT of the entire Python AI service.                               ║
║  When you run `uvicorn main:app --host 0.0.0.0 --port 8000`,            ║
║  Python loads THIS file first and builds the app from it.               ║
║                                                                          ║
║  THREE RESPONSIBILITIES:                                                 ║
║  1. CREATE the FastAPI application with all metadata                     ║
║  2. STARTUP tasks: connect to Qdrant, launch Kafka consumer             ║
║  3. REGISTER all routers (URL groups) with the app                      ║
║                                                                          ║
║  WHAT IS FASTAPI?                                                        ║
║  FastAPI is an async Python web framework (like Express.js for Node).   ║
║  It provides:                                                            ║
║  - HTTP routing (URL → function)                                         ║
║  - Request body parsing (JSON → Python objects via Pydantic)            ║
║  - Response serialization (Python objects → JSON)                       ║
║  - Auto-generated Swagger documentation at GET /docs                    ║
║  - ASGI server compatibility (uvicorn runs it)                          ║
║                                                                          ║
║  WHAT IS UVICORN?                                                        ║
║  Uvicorn is an ASGI server — it handles the low-level TCP networking    ║
║  and HTTP protocol parsing. FastAPI doesn't run itself; uvicorn runs it.║
║  Like: Node runs Express.js. Uvicorn runs FastAPI.                      ║
║                                                                          ║
║  SERVICE PORTS:                                                          ║
║    Python AI Service: port 8000 (HTTP)                                  ║
║    Go Gateway:        port 8080 (HTTP)                                  ║
║    Kafka:             port 9092 (TCP)                                   ║
║    Qdrant:            port 6333 (HTTP)                                  ║
║    PostgreSQL:        port 5432 (TCP)                                   ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# ── Standard library imports ───────────────────────────────────────────────────
import asyncio  # Python's async programming framework (coroutines, event loop, tasks)
import os       # os.getenv() reads environment variables from the .env file

# asynccontextmanager: a Python decorator that turns an async generator into a
# context manager. Used for FastAPI's lifespan hook (startup + shutdown logic).
# An "async context manager" is the async version of Python's `with` statement.
from contextlib import asynccontextmanager

# ── Third-party libraries ──────────────────────────────────────────────────────
# python-dotenv: reads your .env file and loads all key=value pairs into
# Python's os.environ dictionary. This means os.getenv("ANTHROPIC_API_KEY")
# works even though ANTHROPIC_API_KEY is in .env, not the shell environment.
# CRITICAL: load_dotenv() MUST run before any other code that calls os.getenv().
# That's why it's at the top level here, before all other imports.
from dotenv import load_dotenv

# FastAPI: the main web framework class.
# app = FastAPI(...) creates the application object.
from fastapi import FastAPI

# CORSMiddleware: handles Cross-Origin Resource Sharing headers.
# Needed when the frontend (on port 3000) calls the API (on port 8000).
# Browsers enforce CORS — they block cross-origin requests unless the server
# explicitly allows them via "Access-Control-Allow-Origin" response headers.
from fastapi.middleware.cors import CORSMiddleware


# ── Load .env BEFORE everything else ──────────────────────────────────────────
# IMPORTANT: This line must execute BEFORE any import that reads env variables.
# "Reason: os.getenv() reads from os.environ at CALL TIME, not import time.
# But if a module's module-level code calls os.getenv() during import,
# those reads happen at import time → must be loaded before those imports.
# Safe practice: load_dotenv() as early as possible in the entry point.
#
# What load_dotenv() does:
#   1. Finds the .env file (looks in current directory, then parent directories)
#   2. Parses each KEY=VALUE line
#   3. Calls os.environ.setdefault(KEY, VALUE) for each pair
#   setdefault means: only set if not already in environment (existing env vars win)
load_dotenv()


# ── Import all route handlers (routers) ───────────────────────────────────────
# WHAT ARE ROUTERS?
# FastAPI lets you break routes into separate files using APIRouter.
# Each file in routers/ is a "router" — a mini application with its own routes.
# We import each router and attach them to the main app below.
#
# ARCHITECTURE MENTAL MODEL:
# main.py = the "shell" that assembles all the pieces
# routers/ = the actual feature implementations
# agents/ = the AI agent logic
# rag/   = retrieval-augmented generation (vector search)
# integrations/ = external API clients

from routers import agents, inventory, marketing, negotiate, health
# These routers expose their APIRouter as `router`, so we import them differently:
from routers.fraud import router as fraud_router         # POST /fraud/score, /fraud/dispute/respond
from routers.cart_recovery import router as cart_recovery_router  # POST /cart-recovery/generate-email
from routers.seo import router as seo_router             # POST /seo/generate, /seo/bulk-generate

# The Kafka consumer for PokémonTool events (runs as background task)
from consumers.pokemon_events import pokemon_event_consumer


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: Lifespan (Startup + Shutdown)
# ═══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan event handler — runs startup code when the server starts,
    and shutdown code when the server stops.

    WHY @asynccontextmanager?
    FastAPI's modern lifespan API uses an async context manager.
    The pattern is:
      - Code BEFORE `yield` = startup logic
      - `yield` = the server runs here (handling HTTP requests)
      - Code AFTER `yield` = shutdown cleanup

    Alternative (older, deprecated): @app.on_event("startup") and @app.on_event("shutdown")
    We use the modern lifespan approach.

    WHY DOES STARTUP CODE MATTER?
    Some things MUST be initialized before we can serve requests:
      - Qdrant: needs its vector collection to exist before we can use RAG
      - Kafka consumer: must be running before PokémonTool events can be processed
    If we don't do this here, the first request might fail because the database
    isn't ready yet.

    THE DECORATOR CHAIN:
    @asynccontextmanager turns `async def lifespan(...)` into an async context manager.
    FastAPI calls it as: `async with lifespan(app):` internally.
    The `app` parameter is the FastAPI instance being started.
    """
    # ── STARTUP BLOCK (runs once when uvicorn starts) ─────────────────────────
    print("🤖 NexusOS AI Service starting...")

    # Initialize Qdrant vector database collection.
    # WHAT IS QDRANT?
    # A vector database designed for similarity search.
    # NexusOS uses it to store semantic embeddings of past support tickets,
    # product documentation, and store policies.
    # When a customer asks "what's your return policy?", we search Qdrant
    # for similar documents and return the matching policy text as context to the LLM.
    #
    # We import here (inside the function) to avoid circular imports.
    # rag.pipeline imports from agents, which might import from main.
    # Importing late (lazily) prevents that circular dependency chain.
    from rag.pipeline import init_qdrant
    await init_qdrant()
    # `await` waits for the async Qdrant initialization to complete.
    # If we didn't await it, initialization would start but we'd move on before it finished.
    print("✅ Qdrant vector collection initialized (ready for RAG)")

    # Start the PokémonTool Kafka consumer as a background async task.
    # WHAT IS asyncio.create_task()?
    # It schedules a coroutine to run concurrently in the SAME event loop.
    # The consumer runs its infinite loop (reading Kafka messages) while
    # the FastAPI server simultaneously handles HTTP requests.
    # They don't block each other because asyncio is COOPERATIVE — they yield
    # control to each other at every `await` point.
    #
    # HOW IT'S DIFFERENT FROM THREADING:
    # Threads run truly in parallel (different CPU cores, or interleaved).
    # asyncio tasks run on ONE thread but yield control at await points.
    # For IO-bound work (network calls = Kafka, HTTP to LLM APIs), asyncio
    # is MORE EFFICIENT than threads (no thread overhead, no GIL issues).
    #
    # WHY WE CHECK KAFKA_BROKER BEFORE STARTING:
    # If there's no Kafka broker configured, starting the consumer would just
    # print errors forever. We skip it to avoid noise in development.
    kafka_broker = os.getenv("KAFKA_BROKER") or os.getenv("KAFKA_BROKERS")
    if kafka_broker:
        # create_task() launches the consumer's `run()` coroutine.
        # It returns a Task object we could store to cancel it later.
        # We don't need to store it — the task runs until the event loop exits.
        asyncio.create_task(pokemon_event_consumer.run())
        print("✅ PokémonTool Kafka consumer started (background task)")
    else:
        # Graceful degradation: no Kafka = no event consumer.
        # The HTTP server still runs. Fraud scoring, SEO, cart recovery all work.
        # Only the automated market intelligence is disabled.
        print("⚠️  KAFKA_BROKER not set — PokémonTool event consumer disabled")

    port = os.getenv("PORT_AI", "8000")
    print(f"🚀 NexusOS AI Service ready on http://0.0.0.0:{port}")
    print(f"📖 API Documentation: http://localhost:{port}/docs")

    # yield: this is where the server runs and handles requests.
    # Everything before yield = startup. Everything after = shutdown.
    # The FastAPI application is ACTIVE between yield and the end of the function.
    yield

    # ── SHUTDOWN BLOCK (runs once when uvicorn stops: Ctrl+C, SIGTERM, docker stop) ──
    # When uvicorn receives SIGTERM (from `docker stop` or `kill <pid>`):
    #   1. Stops accepting new requests
    #   2. Waits for in-flight requests to complete (with a timeout)
    #   3. Resumes here for cleanup
    # The Kafka consumer's asyncio Task is automatically cancelled when the event loop
    # shuts down — aiokafka's consumer.stop() is called in the `finally` block in
    # pokemon_events.py, ensuring clean offset commits.
    print("🛑 NexusOS AI Service shutting down cleanly...")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: Create the FastAPI Application
# ═══════════════════════════════════════════════════════════════════════════════

# FastAPI(...) creates the WSGI/ASGI application object.
# This is the main app object that uvicorn runs.
# All routers, middleware, and event hooks are registered on this object.
app = FastAPI(
    # title: appears in the Swagger UI header and OpenAPI JSON spec
    title="NexusOS AI Service",

    # description: appears in Swagger UI below the title.
    # This is what shows up at /docs when developers explore the API.
    description=(
        "🤖 Autonomous AI operating system for Shopify merchants. "
        "Features: multi-agent content generation, A2A commerce negotiation, "
        "RAG-powered support, predictive inventory, fraud detection, "
        "cart recovery, AI SEO, and PokémonTool TCG market intelligence."
    ),

    # version: shown in Swagger UI and OpenAPI JSON.
    # Useful for API clients to check compatibility.
    version="2026.2.0",

    # lifespan: the startup/shutdown handler we defined above.
    # FastAPI calls it as an async context manager around the server's lifetime.
    lifespan=lifespan,

    # docs_url: where to serve the interactive Swagger UI.
    # Visit http://localhost:8000/docs to try all endpoints in the browser.
    docs_url="/docs",

    # redoc_url: alternative ReDoc documentation (better for reading).
    # Visit http://localhost:8000/redoc for the nicer documentation view.
    redoc_url="/redoc",
)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: Add Middleware
# ═══════════════════════════════════════════════════════════════════════════════

# CORS MIDDLEWARE EXPLAINED:
# CORS = Cross-Origin Resource Sharing. A browser security feature.
#
# SCENARIO WITHOUT CORS (browser blocks it):
#   React frontend: http://localhost:3000
#   FastAPI backend: http://localhost:8000
#   Browser: "These are different ports = different origins. BLOCKED."
#
# SCENARIO WITH CORS MIDDLEWARE (works):
#   FastAPI adds to every response:
#     Access-Control-Allow-Origin: http://localhost:3000
#     Access-Control-Allow-Methods: GET, POST, ...
#   Browser checks for this header: "Server allows it. OK."
#
# SETTINGS:
# allow_origins: which frontends can call us.
#   FRONTEND_URL env var: set to "https://your-shopify-app.com" in production.
#   Default "*": allows ANY origin (fine for development, less safe in production).
# allow_methods: which HTTP methods are allowed (GET/POST/PUT/DELETE/OPTIONS).
# allow_headers: which request headers are allowed.
#   "Authorization": needed for JWT token auth.
#   "X-Internal-Secret": needed for service-to-service calls.
# allow_credentials: True means cookies and Authorization headers are allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Internal-Secret"],
    allow_credentials=True,  # allow cookies and auth headers cross-origin
)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: Register Routers
# ═══════════════════════════════════════════════════════════════════════════════
#
# app.include_router() mounts a router onto the app.
# The router's prefix is prepended to all its route paths.
#
# EXAMPLE:
#   agents.router has: @router.post("/support/resolve")
#   We include it with: app.include_router(agents.router, prefix="/agents")
#   Result: POST /agents/support/resolve
#
# WHY SEPARATE ROUTERS?
# Instead of one 2000-line main.py with all routes, each feature lives
# in its own file. This is the SEPARATION OF CONCERNS principle:
#   - fraud.py knows everything about fraud detection
#   - seo.py knows everything about SEO generation
#   - Neither knows about the other
# Adding a new feature = add a new router file, one include_router() line here.

# ── Health Check ──────────────────────────────────────────────────────────────
# GET /health → returns {status: "ok", services: {qdrant: "up", pokemon: "up", ...}}
# Used by Docker healthcheck, load balancers, and monitoring dashboards.
app.include_router(health.router, tags=["Infrastructure"])

# ── AI Agent Triggers ─────────────────────────────────────────────────────────
# POST /agents/support/resolve → resolve a customer support ticket
# POST /agents/logistics/restock → trigger inventory restock evaluation
# POST /agents/finance/margin → financial margin analysis
app.include_router(agents.router, prefix="/agents", tags=["AI Agents"])

# ── A2A Commerce Negotiation ──────────────────────────────────────────────────
# POST /negotiate/offer   → receive a B2B price offer from another AI agent
# POST /negotiate/contract → finalize and sign a negotiated contract
app.include_router(negotiate.router, prefix="/negotiate", tags=["A2A Commerce"])

# ── Inventory & Demand Forecasting ───────────────────────────────────────────
# POST /inventory/forecast  → run Prophet ML forecast for a product
# POST /inventory/draft-po  → generate a draft purchase order
app.include_router(inventory.router, prefix="/inventory", tags=["Inventory & Supply"])

# ── Marketing & CRM ───────────────────────────────────────────────────────────
# POST /marketing/segment → AI customer segmentation (VIP, at-risk, etc.)
app.include_router(marketing.router, prefix="/marketing", tags=["Marketing & CRM"])

# ── Fraud Detection & Chargeback Defense ─────────────────────────────────────
# POST /fraud/score           → score an order 0-100 for fraud risk
# POST /fraud/dispute/respond → auto-draft chargeback dispute response
app.include_router(fraud_router, tags=["Fraud & Risk"])

# ── Cart Abandonment Recovery ─────────────────────────────────────────────────
# POST /cart-recovery/generate-email → generate hyper-personalized recovery email
app.include_router(cart_recovery_router, tags=["Cart Recovery"])

# ── AI SEO & Product Descriptions ────────────────────────────────────────────
# POST /seo/generate      → generate SEO package for one product
# POST /seo/bulk-generate → generate SEO for up to 50 products in parallel
app.include_router(seo_router, tags=["SEO & Content"])


# ═══════════════════════════════════════════════════════════════════════════════
# PART 5: Development Runner
# ═══════════════════════════════════════════════════════════════════════════════

# `if __name__ == "__main__"` is a Python idiom meaning:
# "Only run this block if this script is executed directly."
# When uvicorn imports this module (uvicorn main:app), __name__ = "main", NOT "__main__".
# So this block is SKIPPED when run via uvicorn.
# When you run `python main.py` directly, __name__ = "__main__" → this runs.
if __name__ == "__main__":
    # Import uvicorn only when needed (not required at import time)
    import uvicorn

    uvicorn.run(
        # "main:app" tells uvicorn to import `app` from `main.py`
        # This is the same as `from main import app` then running it.
        "main:app",

        # host="0.0.0.0": listen on ALL network interfaces.
        # "0.0.0.0" means: accept connections from localhost, LAN, and internet.
        # "127.0.0.1" (localhost only) would prevent Docker from accessing it.
        host="0.0.0.0",

        # Port 8000: where the API will be accessible.
        # int() converts the string from os.getenv() to an integer (uvicorn needs int).
        port=int(os.getenv("PORT_AI", "8000")),

        # reload: auto-restart the server when .py files change.
        # ONLY in development — uses ~2x memory and slower startup.
        # In Docker (PYTHON_ENV != "development"), this is False.
        reload=os.getenv("PYTHON_ENV") == "development",

        # log_level: how verbose the uvicorn access log is.
        # "info" = logs every request. "warning" = only warnings and errors.
        log_level="info",
    )
