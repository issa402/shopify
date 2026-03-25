"""
╔══════════════════════════════════════════════════════════════════════════╗
║  NexusOS ↔ PokémonTool Integration Client (Python)                       ║
║  File: services/ai/integrations/pokemon_client.py                        ║
╠══════════════════════════════════════════════════════════════════════════╣
║  WHAT THIS FILE IS:                                                      ║
║  The Python AI service's "phone" to call PokémonTool's REST API.        ║
║                                                                          ║
║  WHY DOES THE PYTHON SERVICE NEED TO CALL POKÉMONTOOL DIRECTLY?         ║
║  Three places in NexusOS need live Pokemon card market data:            ║
║                                                                          ║
║  1. A2A NEGOTIATION (agents/negotiation.py)                             ║
║     When a buyer's AI agent asks "how much is a Charizard PSA 9?",      ║
║     NegotiationEngine calls get_card_price() to anchor our offer        ║
║     to the REAL market price, not a hardcoded stub price.               ║
║                                                                          ║
║  2. CART RECOVERY (routers/cart_recovery.py)                            ║
║     If someone abandoned a cart with a Charizard, we fetch its current  ║
║     price trend and include: "That Charizard is up 15% this week"       ║
║     in the recovery email. Real data = more urgency = more conversions. ║
║                                                                          ║
║  3. SEO GENERATION (routers/seo.py)                                     ║
║     When generating a product description for a card, we include        ║
║     live market data: "Currently valued at $450 on TCGplayer."         ║
║                                                                          ║
║  HOW WE CALL POKÉMONTOOL:                                               ║
║  PokémonTool is a SEPARATE Go server running on port 3001.             ║
║  It has its own REST API that we call with HTTP GET requests.           ║
║  We NEVER modify PokémonTool's code — we only consume its API.         ║
║                                                                          ║
║  WHY httpx AND NOT requests?                                             ║
║  FastAPI is ASYNC (runs on Python's asyncio event loop).               ║
║  If we used the popular `requests` library inside an async function:     ║
║    async def my_endpoint():                                              ║
║        result = requests.get("...")  ← THIS BLOCKS THE ENTIRE SERVER    ║
║  While waiting for the HTTP response, NO OTHER requests can be handled. ║
║  httpx.AsyncClient.get() is non-blocking: the server handles other     ║
║  requests WHILE waiting for PokémonTool to respond.                     ║
║                                                                          ║
║  DESIGN: Singleton pattern (pokemon_client created once at module level) ║
║  Import it anywhere: from integrations.pokemon_client import pokemon_client ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os      # for os.getenv() to read .env variables
import logging # Python's built-in logging system (writes structured logs vs print())
from typing import Optional  # Optional[X] = "this value is either type X or None"

# httpx: async-native HTTP client for Python.
# Replaces the synchronous `requests` library when working in async contexts.
# API surface is similar to `requests` (familiar) but all methods are awaitable.
import httpx

# __name__ → the module's fully qualified name (e.g., "integrations.pokemon_client")
# Using getLogger(__name__) creates a logger named after the module.
# This means log messages automatically say which file they came from.
# Example log output: "[integrations.pokemon_client] ⚠️ Card not found"
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: Configuration Constants
# ═══════════════════════════════════════════════════════════════════════════════

# Where PokémonTool is running.
# In Docker Compose: containers talk to each other by SERVICE NAME.
# The PokémonTool Go server's Docker service name would be "pokemon-server".
# In local dev (both running on your laptop): "http://localhost:3001"
# os.getenv(key, default) reads from .env; falls back to default if not set.
POKEMONTOOL_URL = os.getenv("POKEMONTOOL_API_URL", "http://localhost:3001")

# Optional shared secret for internal API calls.
# PokémonTool can (optionally) require this header to distinguish
# NexusOS's internal calls from external public API calls.
# Both sides share the same secret — set it identically in both .env files.
POKEMONTOOL_SECRET = os.getenv("POKEMONTOOL_API_SECRET", "")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: Data Model
# ═══════════════════════════════════════════════════════════════════════════════

class CardPrice:
    """
    Represents a Pokemon card's current market price and trend data.

    WHY A CUSTOM CLASS INSTEAD OF JUST A DICT?
    Dicts: `card["price_tcgplayer"]` — no autocomplete, typo-prone, no type safety
    Class: `card.price_tcgplayer`    — autocomplete, @property logic, self-documenting

    The `best_market_price` property encapsulates business logic:
    "prefer TCGplayer price over eBay" — without this class, every caller
    would need to implement that logic themselves (duplication risk).

    WHAT THE FIELDS MEAN:
    card_id         → PokémonTool's internal database ID for the card
    name            → Card name e.g. "Charizard Base Set Shadowless"
    set_name        → Which set e.g. "Base Set", "Base Set 2"
    price_tcgplayer → Current market price on TCGplayer.com
                      (dedicated TCG marketplace — most reliable data)
    price_ebay      → Average of recent eBay sold listings
                      (broader market but includes auctions, may be noisier)
    trend_label     → "RISING" | "STABLE" | "FALLING"
                      PokémonTool's analytics engine computes this from
                      price change over the past 7/30 days
    trending_score  → -100 to +100. Magnitude of the trend.
                      100 = strong uptrend. -100 = strong downtrend. 0 = flat.
    """

    def __init__(self, data: dict):
        """
        Construct a CardPrice from a raw JSON dict from PokémonTool's API.

        dict.get(key, default) → returns value for key, or default if key not found.
        This gracefully handles partial API responses (missing fields = default value,
        not KeyError crash).

        float(value) and int(value) convert the JSON values to Python numbers.
        JSON arrives as strings in some APIs; float/int ensures correct types.
        """
        self.card_id: str = data.get("card_id", "")
        self.name: str = data.get("name", "")
        self.set_name: str = data.get("set_name", "")
        self.price_tcgplayer: float = float(data.get("price_tcgplayer", 0.0))
        self.price_ebay: float = float(data.get("price_ebay", 0.0))
        self.trend_label: str = data.get("trend_label", "STABLE")   # default: assume stable
        self.trending_score: int = int(data.get("trending_score", 0))  # default: 0 (neutral)

    @property
    def best_market_price(self) -> float:
        """
        Returns the most reliable current market price.

        WHY THIS LOGIC?
        TCGplayer is a dedicated Pokemon card marketplace with real-time pricing.
        It's considered the "official" price reference by most collectors.
        eBay data is noisier (includes auctions, old listings, inflated BIN listings).

        We prefer TCGplayer when available (price_tcgplayer > 0).
        If TCGplayer data wasn't scraped/available, fall back to eBay price.

        WHAT IS @property?
        In Python, @property makes a method callable WITHOUT parentheses.
        Instead of: card.best_market_price() — you call card.best_market_price
        It "looks like" an attribute but runs code. Used for computed values.
        """
        if self.price_tcgplayer > 0:
            return self.price_tcgplayer  # preferred: dedicated TCG marketplace
        return self.price_ebay           # fallback: broader market average

    @property
    def is_rising(self) -> bool:
        """
        Simple boolean: is this card's price trending upward?

        Used in negotiation engine: if is_rising → reduce discount.
        Why give a 20% discount when the card will be worth more tomorrow?
        """
        return self.trend_label == "RISING"

    @property
    def is_falling(self) -> bool:
        """
        Simple boolean: is this card's price trending downward?

        Used in cart recovery: if is_falling → might trigger "buy now, price dropping"
        messaging instead of "price is rising, act fast" messaging.
        """
        return self.trend_label == "FALLING"


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: The HTTP Client Class
# ═══════════════════════════════════════════════════════════════════════════════

class PokemonToolClient:
    """
    Async HTTP client for the PokémonTool API.

    PATTERN: Centralized HTTP client class.
    Instead of repeating `async with httpx.AsyncClient(...) as client:` everywhere,
    all PokémonTool API calls funnel through this class.
    Benefits:
    - One place to change the base URL, headers, timeout settings
    - One place to add retry logic later
    - One place to add logging/metrics
    - Easy to mock in tests (swap the real client for a fake one)

    HOW httpx WORKS (vs requests):
    requests: `response = requests.get(url)`          ← BLOCKING, synchronous
    httpx:    `response = await client.get(url)`      ← NON-BLOCKING, async

    The `await` keyword tells Python's asyncio event loop:
    "Start this HTTP request, but while waiting for the network response,
    go handle other incoming requests. Come back when the response arrives."
    This allows one server process to handle thousands of concurrent users.
    """

    def __init__(self):
        # These headers are sent with EVERY request to PokémonTool.
        # They tell PokémonTool who we are and what format we expect back.
        self._headers = {
            # X-Internal-Secret: identifies this request as from NexusOS.
            # PokémonTool verifies this to prevent random external callers
            # from using the internal API routes.
            "X-Internal-Secret": POKEMONTOOL_SECRET,
            # Accept: tells the server we want JSON back (not HTML or XML)
            "Accept": "application/json",
            # User-Agent: best practice to identify your client.
            # Helps PokémonTool's access logs show "NexusOS called us"
            # instead of an anonymous request.
            "User-Agent": "NexusOS-AI/2026.1.0",
        }

        # httpx.Timeout(5.0): 5 second TOTAL timeout per request.
        # If PokémonTool doesn't respond in 5 seconds → TimeoutException.
        # WHY A TIMEOUT? Without one, a slow/hung PokémonTool could make
        # our A2A endpoints hang forever waiting, blocking the request.
        # 5 seconds is long enough for a real response, short enough to fail fast.
        self._timeout = httpx.Timeout(5.0)


    async def get_card_price(self, card_name: str) -> Optional[CardPrice]:
        """
        Fetch real-time price and trend data for a specific Pokemon card.

        USED BY:
        - agents/negotiation.py → to price A2A offers correctly
        - routers/cart_recovery.py → to enrich abandonment emails with market data
        - routers/seo.py → to include live price in product descriptions

        HOW THE URL IS BUILT:
        POKEMONTOOL_URL = "http://localhost:3001"
        url = "http://localhost:3001/api/cards/search"
        params = {"q": "Charizard Base Set"}
        → Final GET: http://localhost:3001/api/cards/search?q=Charizard+Base+Set

        Args:
            card_name: The card to search for. PokémonTool does fuzzy matching,
                       so partial names work: "Charizard" returns all Charizard cards.

        Returns:
            CardPrice object with market data.
            Returns None if card not found or on any error.
            None is the signal to fall back to default pricing.
        """
        url = f"{POKEMONTOOL_URL}/api/cards/search"
        # params dict → httpx converts this to query string: ?q=Charizard+Base+Set
        params = {"q": card_name}

        try:
            # `async with` = an async context manager.
            # Opens the HTTP client → makes the request → closes the client.
            # `async with` is the async equivalent of Python's regular `with` statement.
            # Even if an exception is raised, the client is properly closed.
            async with httpx.AsyncClient(headers=self._headers, timeout=self._timeout) as client:
                # `await client.get(url, params=params)`:
                # - Sends the GET request to PokémonTool
                # - `await` yields control to event loop while waiting for response
                # - Returns an httpx.Response object when data arrives
                response = await client.get(url, params=params)

            # HTTP Status Codes:
            # 200 = OK (success)
            # 404 = Not Found (card doesn't exist in PokémonTool's database)
            # 500 = Server Error (PokémonTool had a bug)
            # 503 = Service Unavailable (overloaded or shutting down)
            if response.status_code == 404:
                # Normal case: card simply doesn't exist in PokémonTool yet.
                # Log at INFO level (not WARNING — it's not an error, just absence of data)
                logger.info(f"[pokemon] Card '{card_name}' not found in PokémonTool")
                return None  # Caller uses None as signal to fall back to default price

            if response.status_code != 200:
                # Unexpected non-200, non-404 status. Log as WARNING.
                logger.warning(
                    f"[pokemon] get_card_price returned status {response.status_code} "
                    f"for card='{card_name}'"
                )
                return None

            # response.json() parses the JSON response body into a Python dict or list.
            # PokémonTool's search returns a LIST of matching cards (multiple matches possible).
            data = response.json()
            # Normalize to list: if server returned a single dict, wrap it in a list.
            # `isinstance(data, list)` checks if data IS a list object.
            # If not (e.g., it's a dict), wrap it: [data]
            cards = data if isinstance(data, list) else [data]

            if not cards:
                # Empty list = search returned no results
                logger.info(f"[pokemon] No results for card='{card_name}'")
                return None

            # Take the first result — PokémonTool returns results sorted by relevance.
            # cards[0] = the most relevant match to the search query.
            card = CardPrice(cards[0])
            logger.info(
                f"[pokemon] {card.name}: TCGPlayer=${card.price_tcgplayer:.2f} "
                f"eBay=${card.price_ebay:.2f} trend={card.trend_label}"
            )
            return card

        # ── Exception handling: specific error types ─────────────────────────
        # httpx raises different exceptions for different failures.
        # We catch the SPECIFIC ones to give useful error messages.

        except httpx.TimeoutException:
            # PokémonTool didn't respond within 5 seconds.
            # Could be overloaded, network issues, or the container is starting.
            logger.error(f"[pokemon] Timeout fetching price for '{card_name}' — PokémonTool may be slow")
            return None  # Caller falls back to default price

        except httpx.ConnectError:
            # Can't establish TCP connection to PokémonTool.
            # The container isn't running, or the URL is wrong.
            logger.error(f"[pokemon] Cannot connect to PokémonTool at {POKEMONTOOL_URL}")
            return None

        except Exception as e:
            # Catch-all for any other unexpected errors (JSON parse error, etc.)
            # Log with repr to get full error class and message.
            logger.error(f"[pokemon] Unexpected error in get_card_price: {e}")
            return None


    async def get_deals(self) -> list[dict]:
        """
        Fetch today's deal cards from PokémonTool.

        WHAT IS A "DEAL"?
        PokémonTool's analytics engine runs hourly and compares current eBay/TCGplayer
        listing prices to the card's 30-day moving average price.
        Cards selling 20%+ below their moving average = "deals."

        Example: Charizard's 30-day avg = $450. Someone listed it on eBay for $320.
        Savings = ($450 - $320) / $450 = 28.9% below market → it's a deal!

        USED BY: consumers/pokemon_events.py._handle_deal()
        When a deal event arrives via Kafka, LogisticsAgent evaluates if we should buy.

        THE DATA IS PRE-COMPUTED:
        PokémonTool already found these deals — we're just reading the results.
        The heavy lifting (crawling eBay, comparing prices) is done in PokémonTool.

        Returns:
            List of deal dicts with keys: card_name, market_price, best_price,
            savings_pct, ebay_url, deal_date.
            Returns EMPTY LIST on any error (this is "fail safe" / "open default").
            Missing deal data ≠ broken system. Agents just have less to work with.
        """
        url = f"{POKEMONTOOL_URL}/api/deals"

        try:
            async with httpx.AsyncClient(headers=self._headers, timeout=self._timeout) as client:
                response = await client.get(url)

            if response.status_code != 200:
                logger.warning(f"[pokemon] get_deals returned status {response.status_code}")
                return []  # empty list = no deals available right now

            deals = response.json()
            logger.info(f"[pokemon] Fetched {len(deals)} active deals from PokémonTool")
            # Ensure we return a list (defensive: if server returned dict for some reason)
            return deals if isinstance(deals, list) else []

        except Exception as e:
            # Deals are a "nice to have." If PokémonTool is down, the rest of NexusOS
            # continues operating — we just miss opportunity alerts temporarily.
            logger.error(f"[pokemon] Failed to fetch deals: {e}")
            return []  # empty list = graceful degradation


    async def get_trending(self, limit: int = 20) -> list[CardPrice]:
        """
        Fetch the top N trending Pokemon cards right now.

        TRENDING = cards whose prices are moving significantly (up OR down).
        PokémonTool scores each card -100 to +100.
        This endpoint returns cards sorted by abs(trending_score) DESC —
        the most strongly moving cards appear first.

        WHY CARE ABOUT TRENDING?
        - RISING cards: raise our Shopify listing prices before buyers realize
        - FALLING cards: run flash sales quickly to liquidate before price drops further
        - Inform what cards to source next (trending up = demand is high)

        USED BY: consumers/pokemon_events.py._handle_trend()
        When a trend event arrives from Kafka, we call this to get the full picture.

        Args:
            limit: How many trending cards to return. 20 is usually enough for
                   a single market review. Use higher numbers for bulk analysis.

        Returns:
            List of CardPrice objects. Empty list on error.
        """
        url = f"{POKEMONTOOL_URL}/api/cards/trending"
        params = {"limit": limit}

        try:
            async with httpx.AsyncClient(headers=self._headers, timeout=self._timeout) as client:
                response = await client.get(url, params=params)

            if response.status_code != 200:
                logger.warning(f"[pokemon] get_trending returned status {response.status_code}")
                return []

            cards_data = response.json()
            # List comprehension: create a CardPrice object from each dict in the response.
            # `cards_data if isinstance(cards_data, list) else []` → defensive: handle non-list response
            cards = [CardPrice(c) for c in (cards_data if isinstance(cards_data, list) else [])]
            logger.info(f"[pokemon] Fetched {len(cards)} trending cards")
            return cards

        except Exception as e:
            logger.error(f"[pokemon] Failed to fetch trending cards: {e}")
            return []


    async def health_check(self) -> bool:
        """
        Check if PokémonTool is running and reachable.

        USED BY: routers/health.py (GET /health endpoint)
        The NexusOS health endpoint checks all dependencies and reports
        their status. This lets the merchant dashboard show:
          ✅ NexusOS Gateway: healthy
          ✅ PokémonTool: connected
          ❌ PokémonTool: unreachable

        SHORTER TIMEOUT:
        Health checks should be fast. We use 2 seconds instead of 5.
        If something takes 5 seconds to respond to a ping, it's not really "healthy."

        Returns:
            True  = PokémonTool responded with HTTP 200
            False = timeout, connection error, or non-200 response
        """
        try:
            # Inline httpx client with a shorter timeout (2s vs our usual 5s)
            # httpx.Timeout(2.0) = 2 second total timeout for this specific call
            async with httpx.AsyncClient(timeout=httpx.Timeout(2.0)) as client:
                response = await client.get(f"{POKEMONTOOL_URL}/health")
            # Return True only if status code is exactly 200 (not 201, 204, etc.)
            return response.status_code == 200
        except Exception:
            # ANY exception = PokémonTool is unreachable.
            # We don't log here because health_check may be called frequently,
            # and we don't want to spam logs if PokémonTool is briefly down.
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: Module-Level Singleton
# ═══════════════════════════════════════════════════════════════════════════════

# SINGLETON PATTERN:
# We create ONE PokemonToolClient instance at module load time.
# All files that do `from integrations.pokemon_client import pokemon_client`
# get the SAME instance — they share one HTTP connection pool.
# This is more efficient than creating a new client for every function call.
#
# HOW TO USE THIS IN OTHER FILES:
#   from integrations.pokemon_client import pokemon_client
#   card = await pokemon_client.get_card_price("Charizard")
#   deals = await pokemon_client.get_deals()
poker_client_comment = "Import `pokemon_client` (the instance below), not `PokemonToolClient` (the class)"
pokemon_client = PokemonToolClient()
