"""
╔══════════════════════════════════════════════════════════════════════════╗
║  NexusOS — PokémonTool Kafka Event Consumer                              ║
║  File: services/ai/consumers/pokemon_events.py                           ║
╠══════════════════════════════════════════════════════════════════════════╣
║  WHAT IS THIS FILE?                                                      ║
║  A background worker that permanently listens to three Kafka topics      ║
║  and runs AI agents to take action on PokémonTool market intelligence.  ║
║                                                                          ║
║  THE FULL FLOW:                                                           ║
║  PokémonTool finds a deal on eBay                                       ║
║    ↓                                                                     ║
║  bridge.go posts HTTP to NexusOS Gateway                                ║
║    ↓                                                                     ║
║  Gateway's pokemon/handler.go puts it on Kafka "pokemon.deals"          ║
║    ↓                                                                     ║
║  THIS FILE reads the Kafka message                                       ║
║    ↓                                                                     ║
║  _handle_deal() → runs LogisticsAgent + FinanceAgent                    ║
║    ↓                                                                     ║
║  Creates draft purchase order in approval_queue table                   ║
║    ↓                                                                     ║
║  Merchant sees it in dashboard, clicks ✅ or ❌                          ║
║                                                                          ║
║  THREE TOPICS = THREE AUTOMATIC AI WORKFLOWS:                           ║
║  pokemon.deals         → evaluate if we should BUY a card               ║
║  pokemon.trends        → adjust our SHOPIFY LISTING PRICES              ║
║  pokemon.price-alerts  → check if our prices are OUT OF SYNC            ║
║                                                                          ║
║  HOW IT RUNS ALONGSIDE FASTAPI:                                         ║
║  FastAPI is the HTTP server. This consumer is an asyncio background     ║
║  task. They share the SAME event loop.                                   ║
║  In main.py:                                                             ║
║    asyncio.create_task(pokemon_event_consumer.run())                    ║
║  → Runs forever in the background while FastAPI handles HTTP requests   ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# ── Standard library imports ───────────────────────────────────────────────────
import asyncio   # Python's async/concurrency framework. Core of modern async Python.
                  # asyncio.sleep() = async version of time.sleep() (non-blocking)
                  # asyncio.to_thread() = run a sync function in a thread pool
                  # asyncio.create_task() = start a background coroutine alongside current code
import json      # json.loads() converts JSON string to Python dict
import logging   # Python's structured logging system
import os        # os.getenv() reads .env environment variables
from datetime import datetime  # used for timestamps in log messages
from typing import Optional     # type hint: Optional[str] = str | None

# ── aiokafka: async Kafka client for Python ────────────────────────────────────
# WHY aiokafka INSTEAD OF kafka-python?
# kafka-python is synchronous: consumer.poll_messages() BLOCKS until a message arrives.
# If we called that inside an async function, it would FREEZE FastAPI entirely.
# aiokafka.AIOKafkaConsumer is async: `async for message in consumer` yields control
# to the event loop between messages, allowing FastAPI to handle HTTP requests simultaneously.
# Both run in the SAME asyncio event loop — they interleave without blocking each other.
from aiokafka import AIOKafkaConsumer

# ── Internal NexusOS imports ───────────────────────────────────────────────────
# The singleton PokémonTool client (for fetching live card data)
from integrations.pokemon_client import pokemon_client

# Agent runner functions from crew.py
# run_logistics_agent("task") → runs LogisticsAgent with that task description
# run_finance_agent("task")   → runs FinanceAgent with that task description
# These are SYNCHRONOUS CrewAI calls — we'll wrap them with asyncio.to_thread()
from agents.crew import run_logistics_agent, run_finance_agent

# NegotiationEngine: used to refresh pricing data for any in-progress negotiations
from agents.negotiation import NegotiationEngine

# Set up logger for this module
logger = logging.getLogger(__name__)  # logger named "consumers.pokemon_events"


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# Where Kafka is running. Same broker address as the Go Gateway uses.
# In Docker Compose: "nexusos-kafka:9092" (container-to-container)
# In local dev: "localhost:9092"
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")

# The three Kafka topics this consumer listens to.
# These topic names MUST match exactly what pokemon/handler.go publishes to.
# If they differ, this consumer will get zero messages (silent failure!).
POKEMON_TOPICS = [
    "pokemon.deals",         # card listed 20%+ below TCGplayer market price
    "pokemon.trends",        # card trending_score crossed ±50 (significant market move)
    "pokemon.price-alerts",  # a user's price threshold alert was triggered
]

# Consumer group ID.
# WHAT IS A CONSUMER GROUP?
# Multiple instances of the Python AI service (for scaling) would all run this consumer.
# Kafka distributes messages across consumers in the SAME group.
# Example: 3 replicas of the AI service → Kafka gives each 1/3 of the messages.
# This is horizontal scaling: more workers = more throughput.
#
# If two consumers had DIFFERENT group IDs, each would get ALL messages independently.
# We use ONE group ID so duplicate processing doesn't happen when we scale up.
CONSUMER_GROUP = "nexusos-ai-pokemon-consumer"


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: Consumer Class
# ═══════════════════════════════════════════════════════════════════════════════

class PokemonEventConsumer:
    """
    Background Kafka consumer that powers NexusOS's autonomous market intelligence.

    DESIGN PRINCIPLE: "Self-healing consumer"
    The outer run() loop catches ALL exceptions and retries after 5 seconds.
    The inner _run_consumer_loop() handles per-message errors gracefully.
    Together: one bad message never kills the consumer,
              and Kafka connection failures self-recover.

    STATE:
    self._running: bool → True while the consumer should keep running.
    self.negotiation_engine: NegotiationEngine → used to refresh pricing context.
    """

    def __init__(self):
        # Create a NegotiationEngine to keep track of pricing context.
        # A2A negotiations in progress need to know the latest card prices.
        self.negotiation_engine = NegotiationEngine()

        # Control flag: set to False to stop the consumer gracefully.
        # This allows main.py's shutdown handler to stop the consumer
        # without forcefully killing the process.
        self._running = False

    async def run(self):
        """
        The main worker loop. Designed to run FOREVER as a background task.

        HOW TO START THIS:
            consumer = PokemonEventConsumer()
            asyncio.create_task(consumer.run())

        WHAT `async def` MEANS:
        `async def run()` declares this as a coroutine — a function that can be
        suspended at `await` points and resumed later.
        You schedule it with asyncio.create_task() — it runs concurrently with
        FastAPI's HTTP handler tasks in the same event loop.

        SELF-HEALING RETRY LOGIC:
        If _run_consumer_loop() crashes (Kafka restarts, network blip, etc.),
        we log the error, wait 5 seconds, then restart the consumer loop.
        This makes the consumer RESILIENT — it recovers from transient failures
        automatically without needing an operator to restart it.

        EXPONENTIAL BACKOFF (future improvement):
        Currently waits 5s always. Production improvement: use exponential backoff:
        5s → 10s → 20s → 40s, capped at 5 minutes. Prevents hammering Kafka
        if it's in a prolonged outage. Not needed for MVP.
        """
        self._running = True
        logger.info(
            "[pokemon-consumer] 🚀 Starting — broker=%s topics=%s",
            KAFKA_BROKER, POKEMON_TOPICS
        )

        # Self-healing infinite loop.
        # Runs while self._running is True (set to False by shutdown handler).
        while self._running:
            try:
                # Run the actual consumer loop — this blocks until it crashes.
                await self._run_consumer_loop()
            except Exception as e:
                # _run_consumer_loop() crashed (connection error, Kafka restart, etc.)
                # Don't exit the outer while loop — just wait and retry.
                logger.error(
                    "[pokemon-consumer] 💥 Consumer loop crashed: %s — retrying in 5s", e
                )
                # asyncio.sleep(5): NON-BLOCKING 5 second wait.
                # Unlike time.sleep(5) which would freeze the event loop,
                # asyncio.sleep() yields control so FastAPI can handle requests
                # while we wait.
                await asyncio.sleep(5)


    async def _run_consumer_loop(self):
        """
        Creates the AIOKafkaConsumer, connects to Kafka, and handles messages forever.

        WHY SEPARATE FROM run()?
        Separation of concerns:
        - run() handles the RETRY logic (what to do when this crashes)
        - _run_consumer_loop() handles the CONSUMER logic (creating, running, cleaning up)
        When _run_consumer_loop() encounters an error, it raises it to run(), which retries.

        HOW AIOKafkaConsumer WORKS:
        1. AIOKafkaConsumer(...): configure the consumer (brokers, group, topics, deserializer)
        2. await consumer.start(): establish TCP connection to Kafka, join consumer group
        3. async for message in consumer: block-less loop; yields each message as it arrives
        4. await consumer.stop(): cleanly commit offsets and close connection
        """
        # *POKEMON_TOPICS unpacks the list as positional arguments.
        # AIOKafkaConsumer("pokemon.deals", "pokemon.trends", "pokemon.price-alerts", ...)
        # Not: AIOKafkaConsumer(["pokemon.deals", ...]) — the list version wouldn't work.
        consumer = AIOKafkaConsumer(
            *POKEMON_TOPICS,
            # bootstrap_servers: the Kafka broker(s) to connect to.
            # "Bootstrap" means these are the initial servers used to discover the full cluster.
            bootstrap_servers=KAFKA_BROKER,

            # group_id: our consumer group name (see constant above for explanation).
            group_id=CONSUMER_GROUP,

            # value_deserializer: how to convert raw bytes from Kafka into Python objects.
            # Kafka stores messages as raw bytes. This lambda:
            # 1. b.decode("utf-8"): bytes → UTF-8 string
            # 2. json.loads(string): JSON string → Python dict
            # So message.value is always a Python dict when we receive it.
            value_deserializer=lambda b: json.loads(b.decode("utf-8")),

            # auto_offset_reset: where to start if we don't know our current offset.
            # This happens when: first ever start, or if offsets expired (after 7 days inactive).
            # "earliest" = start from the very beginning of the topic (don't miss old messages).
            # "latest"   = start from now (skip all messages that arrived before we connected).
            # We use "earliest" so that if this service was restarted, we catch up on any
            # PokémonTool events we missed while it was down.
            auto_offset_reset="earliest",

            # enable_auto_commit=True: Kafka automatically tracks which messages we've read.
            # After we receive a message (the `async for` loop), Kafka marks it committed.
            # On restart, we resume from the last committed offset (not from the beginning).
            # Alternative: manual commit (call .commit() ourselves) for more control.
            # Auto-commit is fine for our use case — we handle per-message errors gracefully.
            enable_auto_commit=True,
        )

        # Establish connection to Kafka and join the consumer group.
        # This is where TCP connection is opened. If Kafka is unreachable, this raises.
        await consumer.start()
        logger.info("[pokemon-consumer] ✅ Kafka consumer connected and listening")

        try:
            # `async for message in consumer`:
            # This is Python's async iteration protocol.
            # As each Kafka message arrives:
            #   - The async for loop "wakes up" with the new message
            #   - We process it (await self._dispatch(...))
            #   - Then "go to sleep" again waiting for the next message
            # Between messages, the event loop is FREE to handle FastAPI requests.
            # This is the key benefit of async — concurrent without multiple threads.
            async for message in consumer:
                # message.topic → which topic this message came from (e.g., "pokemon.deals")
                # message.value → the deserialized dict (our event payload)
                # message.key   → bytes of the partition key (card name)
                # message.offset → position in the partition
                try:
                    # Route the message to the appropriate handler
                    await self._dispatch(message.topic, message.value)
                except Exception as e:
                    # PER-MESSAGE error handling: log and continue.
                    # We NEVER let a single bad message crash the entire consumer.
                    # Reasons a message could fail:
                    #   - Malformed event data
                    #   - AI agent API call failed
                    #   - Database write failed
                    # In all cases: log it and move to the next message.
                    # exc_info=True includes the full Python stack trace in the log.
                    logger.error(
                        "[pokemon-consumer] ❌ Error processing %s message: %s",
                        message.topic, e, exc_info=True
                    )
        finally:
            # ALWAYS stop the consumer when the loop exits.
            # `finally` block runs whether the loop ended normally or raised an exception.
            # consumer.stop() flushes pending offset commits and closes TCP connections.
            # Without this: Kafka would think we're still connected for ~10 minutes.
            await consumer.stop()


    async def _dispatch(self, topic: str, event: dict):
        """
        Route an incoming Kafka message to the correct business logic handler.

        DISPATCHER PATTERN:
        Instead of having one massive function with if/elif/elif chains,
        we use a dispatcher that routes to specialized handlers.
        Each handler is focused on ONE thing: deals, trends, or price alerts.

        Args:
            topic: Kafka topic name ("pokemon.deals", "pokemon.trends", etc.)
            event: Deserialized event dict (the Kafka message value, parsed from JSON)
        """
        # The event_type field in the payload is redundant with the topic name,
        # but we include it for clarity in logs.
        # event.get("event_type", topic) → use event_type if present, else fallback to topic name.
        event_type = event.get("event_type", topic)

        logger.info(
            "[pokemon-consumer] 📬 Processing event: type=%s card=%s",
            event_type,
            event.get("card_name", "unknown")  # default "unknown" if card_name missing
        )

        # Simple if/elif chain to route to the right handler.
        # Each handler is async and awaited — this process messages SEQUENTIALLY
        # (one at a time per consumer, since we await each one).
        # For CPU-bound parallel processing, we'd use asyncio.gather().
        if topic == "pokemon.deals":
            await self._handle_deal(event)
        elif topic == "pokemon.trends":
            await self._handle_trend(event)
        elif topic == "pokemon.price-alerts":
            await self._handle_price_alert(event)
        else:
            logger.warning("[pokemon-consumer] ⚠️ Unknown topic: %s", topic)


    # ═══════════════════════════════════════════════════════════════════════════
    # DEAL HANDLER: "Should we buy this card to resell?"
    # ═══════════════════════════════════════════════════════════════════════════

    async def _handle_deal(self, event: dict):
        """
        Process a deal event: PokémonTool found a card selling 20%+ below market.

        THE FULL AI WORKFLOW:
        1. Extract deal metadata from the event dict
        2. Validate: is this deal worth evaluating? (savings ≥ 15%)
        3. Run LogisticsAgent to decide IF we should buy:
              - "Do we already have too much of this card?"
              - "What's our historical sell-through on this card type?"
              - "With 30-day demand forecast, how many should we target?"
        4. If LogisticsAgent says "buy", escalate to FinanceAgent for financial check:
              - "After eBay buyer fees, shipping, Shopify fees → what's our net margin?"
              - "Does this fit our monthly buy budget?"
              - "If margin > 10%, APPROVE and draft a purchase order."
        5. The draft purchase order lands in the merchant's approvals queue.
           The merchant reviews and clicks ✅ to confirm the buy.

        WHY asyncio.to_thread() FOR AGENT CALLS?
        CrewAI agents (run_logistics_agent, run_finance_agent) are SYNCHRONOUS.
        They use LangChain, which makes blocking HTTP calls to OpenAI/Anthropic.
        If we called them directly in this async function, they'd BLOCK the event loop.
        asyncio.to_thread() runs them in a threadpool:
          - The blocking call happens in a background thread
          - The async function yields control while the thread runs
          - FastAPI and other async tasks continue handling requests
          - When the thread finishes, this coroutine resumes with the result
        This is the correct way to call synchronous code from async context.

        Args:
            event: Dict from the "pokemon.deals" Kafka topic.
                   Fields: card_name, best_price, market_price, savings_pct, ebay_url
        """
        # dict.get(key) returns None if key missing. dict.get(key, default) returns default.
        card_name = event.get("card_name")
        best_price = event.get("best_price", 0.0)    # lowest current eBay listing price
        market_price = event.get("market_price", 0.0) # TCGplayer market price (reference)
        savings_pct = event.get("savings_pct", 0.0)   # % below market
        ebay_url = event.get("ebay_url", "")           # direct link to the eBay listing

        # Basic validation: if essential fields are missing, skip this event.
        # A deal without a card name or price is useless to analyze.
        if not card_name or best_price <= 0:
            logger.warning(
                "[pokemon-consumer] ⚠️ Deal event missing card_name or best_price — skipping"
            )
            return  # `return` exits this async function without raising an exception

        logger.info(
            "[pokemon-consumer] 🎯 Deal: %s at $%.2f (%.1f%% below market $%.2f)",
            card_name, best_price, savings_pct, market_price
        )

        # QUALITY FILTER: don't waste agent API credits on tiny discounts.
        # 15% below market is the threshold we consider "real" deal territory.
        # A 5% price dip could be normal market fluctuation, not a deal.
        # This threshold prevents the AI from spending $0.10 on GPT-4o to analyze
        # a $1 discount on a $20 card.
        if savings_pct < 15.0:
            logger.info(
                "[pokemon-consumer] Deal savings %.1f%% < 15%% threshold — skipping",
                savings_pct
            )
            return

        try:
            # ── Step 1: LogisticsAgent evaluation ─────────────────────────────
            # Build a detailed task description for the agent.
            # The more context we give, the better the reasoning.
            # f-string format: f"text {variable:.2f}" → "text 320.00" (2 decimal floats)
            logistics_task = (
                f"Evaluate purchase opportunity: {card_name} available at ${best_price:.2f} "
                f"on eBay (market price: ${market_price:.2f}, {savings_pct:.1f}% below market). "
                f"eBay listing: {ebay_url}. "
                f"Check our current inventory level for this card. "
                f"Review historical sell-through rate if available. "
                f"Forecast demand for next 30 days. "
                f"Recommend: should we buy? If yes, how many units? Reason clearly."
            )

            # asyncio.to_thread(callable, *args, **kwargs):
            # Runs callable(arg1, arg2) in Python's threadpool executor.
            # Returns an awaitable that resolves to the callable's return value.
            # Essential for calling synchronous CrewAI/LangChain code from async.
            logistics_decision = await asyncio.to_thread(
                run_logistics_agent,   # the synchronous function to call
                logistics_task         # passed as the `task` argument to run_logistics_agent
            )

            logger.info(
                "[pokemon-consumer] LogisticsAgent decision for %s: %s",
                card_name,
                str(logistics_decision)[:200]  # truncate long outputs in logs
            )

            # ── Step 2: FinanceAgent approval ──────────────────────────────────
            # Only escalate if LogisticsAgent's output suggests buying.
            # _should_escalate_to_finance() scans the agent's natural language output
            # for buy/skip signals. Simple heuristic — works well enough for MVP.
            if self._should_escalate_to_finance(logistics_decision):
                finance_task = (
                    f"Review purchase opportunity for {card_name} as recommended by LogisticsAgent. "
                    f"Buy price from eBay: ${best_price:.2f}. Market price: ${market_price:.2f}. "
                    f"LogisticsAgent recommendation: {logistics_decision}. "
                    f"Calculate total landed cost: buy price + ~$12 shipping + "
                    f"eBay buyer protection fee + Shopify transaction fee. "
                    f"Check if net margin after all fees > 10%. "
                    f"If approved: draft a purchase order for merchant review. "
                    f"Format: APPROVED/REJECTED + margin calculation + recommended buy quantity."
                )

                finance_decision = await asyncio.to_thread(
                    run_finance_agent,
                    finance_task
                )

                logger.info(
                    "[pokemon-consumer] FinanceAgent decision for %s: %s",
                    card_name,
                    str(finance_decision)[:200]
                )
                # TODO: parse the FinanceAgent output for "APPROVED" and create a
                # purchase order record in the approval_queue Postgres table.

        except Exception as e:
            # Any exception during agent processing (LLM API error, timeout, etc.)
            # is caught here and logged. The consumer continues to the next message.
            logger.error(
                "[pokemon-consumer] ❌ Agent processing failed for deal %s: %s",
                card_name, e
            )


    # ═══════════════════════════════════════════════════════════════════════════
    # TREND HANDLER: "Should we adjust our Shopify listing prices?"
    # ═══════════════════════════════════════════════════════════════════════════

    async def _handle_trend(self, event: dict):
        """
        Process a trend event: a card's price is significantly rising or falling.

        WHAT GOOD REPRICING DOES FOR THE MERCHANT:
        Charizard Base Set is trending RISING (score: 75, +15% in 7 days).
        If the merchant's Shopify listing still shows the old price ($10,000),
        they're UNDERPRICING relative to market → losing potential revenue.
        NexusOS detects this automatically and suggests updating to $11,200.

        Conversely for FALLING cards: repricing DOWN triggers flash sales
        before the card becomes harder to sell at the old price.

        THRESHOLD:
        We only act on strong trends (|score| > 40).
        Score: -100 to +100. -40 to +40 = normal market noise, not worth acting on.
        Score > 40 or < -40 = real trend, worth investigating.

        Args:
            event: Dict from "pokemon.trends" Kafka topic.
                   Fields: card_name, trend_label, trending_score, price_now, pct_change
        """
        card_name = event.get("card_name")
        trend_label = event.get("trend_label", "STABLE")  # "RISING" | "STABLE" | "FALLING"
        trending_score = event.get("trending_score", 0)    # -100 to +100
        price_now = event.get("price_now", 0.0)            # current market price
        pct_change = event.get("pct_change", 0.0)          # % change over 7 days

        if not card_name:
            logger.warning("[pokemon-consumer] Trend event missing card_name — skipping")
            return

        logger.info(
            "[pokemon-consumer] 📈 Trend: %s → %s (score: %d, Δ%.1f%% to $%.2f)",
            card_name, trend_label, trending_score, pct_change, price_now
        )

        # abs(trending_score): absolute value.
        # We check magnitude regardless of direction (rising OR falling both matter).
        # If |score| < 40, it's not significant enough to act on.
        if abs(trending_score) < 40:
            logger.info(
                "[pokemon-consumer] Trend score %d below action threshold ±40 — skipping",
                trending_score
            )
            return

        try:
            # Build different task descriptions depending on trend direction.
            # The agent needs to know the context to make the right recommendation.

            # Base description applicable to both RISING and FALLING
            action_description = (
                f"Card market trend alert: {card_name} is {trend_label} "
                f"(score: {trending_score}/100, price change: {pct_change:+.1f}% to ${price_now:.2f}). "
                # :+.1f formats float with ALWAYS showing sign: "+15.3" or "-8.7"
                # (regular .1f would show "15.3" and "-8.7" — the :+ forces the + for positives)
            )

            if trend_label == "RISING":
                action_description += (
                    "Check our Shopify listing for this card. If we have it listed, "
                    "consider increasing the price to match market movement. "
                    "Calculate the suggested new price (keep 8-12% margin over current market price). "
                    "If the price change would be >$50, queue for merchant approval first. "
                    "If we don't carry this card but trend is strong (score > 60), "
                    "suggest adding it to our Shopify catalog as a new listing."
                )
            elif trend_label == "FALLING":
                action_description += (
                    "Check our Shopify inventory for this card. "
                    "If we have units in stock, consider running a flash sale (5-10% discount) "
                    "to liquidate inventory before price drops further. "
                    "Flag any active purchase orders for this card for immediate review. "
                    "Recommend halting restocking this item until price stabilizes."
                )

            # Route to FinanceAgent (it's the manager agent — handles pricing decisions).
            # FinanceAgent uses the ProfitCalculatorTool to model margin impacts.
            finance_decision = await asyncio.to_thread(
                run_finance_agent,
                action_description,
            )

            logger.info(
                "[pokemon-consumer] FinanceAgent trend response for %s: %s",
                card_name,
                str(finance_decision)[:200]
            )
            # TODO: If FinanceAgent output contains "UPDATE PRICE", extract the
            # new price and create a price_change record in approval_queue table.

        except Exception as e:
            logger.error(
                "[pokemon-consumer] ❌ Trend processing failed for %s: %s",
                card_name, e
            )


    # ═══════════════════════════════════════════════════════════════════════════
    # PRICE ALERT HANDLER: "Our watched card crossed a price threshold"
    # ═══════════════════════════════════════════════════════════════════════════

    async def _handle_price_alert(self, event: dict):
        """
        Process a price alert: a user-defined price watch triggered.

        CONTEXT:
        In PokémonTool, users can set up price watches:
        "Alert me when Charizard drops below $400."
        When that condition is met, PokémonTool fires a user-facing alert
        AND sends this event to NexusOS via the bridge.go.

        NexusOS decides:
        ─ DIRECTION=BELOW: The card's price just dropped.
            - Is it a 15%+ drop? → Treat as a deal (reuse _handle_deal)
            - Is our Shopify listing still showing the old higher price? → Reprice
        ─ DIRECTION=ABOVE: The card's price just rose.
            - Is our Shopify listing underpriced? → Suggest increasing Shopify price
            - Do we own inventory of this card? → Maybe a good time to sell

        Args:
            event: Dict from "pokemon.price-alerts" topic.
                   Fields: card_name, new_price, old_price, pct_change,
                           direction, marketplace, listing_url
        """
        card_name = event.get("card_name")
        new_price = event.get("new_price", 0.0)     # the new current price
        old_price = event.get("old_price", 0.0)     # what the price was before the alert
        direction = event.get("direction", "")       # "BELOW" or "ABOVE"
        pct_change = event.get("pct_change", 0.0)   # % change (signed)
        marketplace = event.get("marketplace", "unknown")  # "ebay" or "tcgplayer"

        if not card_name:
            logger.warning("[pokemon-consumer] Price alert event missing card_name — skipping")
            return

        logger.info(
            "[pokemon-consumer] 🔔 Price alert: %s %s $%.2f → $%.2f (%.1f%%) on %s",
            card_name, direction, old_price, new_price, pct_change, marketplace
        )

        # If the price dropped 15%+ BELOW old, treat it as a deal opportunity.
        # We reuse the deal handler logic for efficiency — no need to duplicate.
        # abs(pct_change) handles both positive and negative pct_change values:
        # If pct_change = -22.0 (fell 22%), abs(-22.0) = 22.0 >= 15 → deal!
        if direction == "BELOW" and abs(pct_change) >= 15.0:
            # Fetch the real market price from PokémonTool (the alert's old_price
            # might be a user-set threshold, not the actual market price).
            market_data = await pokemon_client.get_card_price(card_name)
            if market_data:
                # Build a synthetic deal event from the alert data.
                # This lets _handle_deal() process it with the exact same logic.
                deal_event = {
                    "card_name": card_name,
                    "best_price": new_price,                    # the fallen price = best current price
                    "market_price": market_data.best_market_price, # real TCGplayer reference
                    "savings_pct": abs(pct_change),              # how far below market
                    "ebay_url": event.get("listing_url", ""),    # direct link if available
                }
                # Await the full deal evaluation workflow
                await self._handle_deal(deal_event)

        # Regardless of direction: mark that this card's price changed.
        # Any in-progress A2A negotiations for this card should use fresh prices.
        # (The negotiation engine fetches fresh data anyway, but this is a signal
        # that a cache invalidation would be appropriate in a production system.)
        logger.info(
            "[pokemon-consumer] ✅ Price alert processed for %s — "
            "negotiation cache marked for refresh",
            card_name
        )


    # ═══════════════════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ═══════════════════════════════════════════════════════════════════════════

    def _should_escalate_to_finance(self, logistics_decision) -> bool:
        """
        Heuristically determine if LogisticsAgent recommended buying.

        WHY HEURISTIC TEXT SCANNING?
        CrewAI agents return natural language text (not JSON).
        LogisticsAgent might respond:
          "This looks like a good opportunity. I recommend purchasing 2 units."
        or:
          "Our inventory is already at capacity. I suggest skipping this deal."

        We scan for positive and negative keywords to classify the recommendation.

        LIMITATIONS:
        Text heuristics can be fooled by complex agent phrasing.
        Production improvement: use structured output format from CrewAI:
          {{"recommendation": "BUY", "quantity": 2, "reasoning": "..."}}
        Then: return parsed_result["recommendation"] == "BUY"

        Args:
            logistics_decision: The string or CrewOutput returned by run_logistics_agent()

        Returns:
            True  = agent recommends buying → escalate to FinanceAgent
            False = agent says skip → don't spend money on FinanceAgent call
        """
        if logistics_decision is None:
            return False

        # str(logistics_decision) handles both string and CrewOutput objects.
        # .lower() converts to lowercase so "BUY" and "buy" both match.
        decision_text = str(logistics_decision).lower()

        # Keywords that indicate a BUY recommendation
        buy_signals = [
            "recommend purchasing",   # "I recommend purchasing 2 units"
            "good opportunity",       # "This is a good opportunity"
            "should buy",             # "We should buy this"
            "purchase approved",      # structured response
            "proceed",                # "Proceed with the purchase"
            "buy",                    # direct keyword
            "acquire",                # "Acquire 1-2 units"
        ]

        # Keywords that indicate a SKIP recommendation
        # We check these FIRST because a "don't buy" signal takes priority.
        skip_signals = [
            "do not",           # "Do not purchase" (also matches "don't")
            "don't",            # "Don't buy"
            "skip",             # "Skip this deal"
            "pass",             # "Pass on this opportunity"
            "overstocked",      # "We're already overstocked on this card"
            "poor demand",      # "Historical demand is poor for this set"
            "margin too low",   # "Margin would be too low"
            "not recommended",  # "Purchase is not recommended"
        ]

        # any(iterable): returns True if ANY element of the iterable is truthy.
        # `signal in decision_text`: True if signal is a substring of decision_text.
        has_buy = any(signal in decision_text for signal in buy_signals)
        has_skip = any(signal in decision_text for signal in skip_signals)

        # Skip signals override buy signals.
        # "This looks like a good opportunity but I don't recommend buying due to margin"
        # → has_buy=True, has_skip=True → return False (skip)
        # Safety > opportunity: better to miss a deal than to make a bad buy.
        if has_skip:
            return False

        # Only buy if we found positive signals AND no negative signals.
        return has_buy


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: Module-Level Singleton
# ═══════════════════════════════════════════════════════════════════════════════

# This creates a SINGLE PokemonEventConsumer instance when this module is first imported.
# In main.py:
#   from consumers.pokemon_events import pokemon_event_consumer
#   asyncio.create_task(pokemon_event_consumer.run())
#
# The instance is shared — only ONE background task runs total.
# You don't create a new PokemonEventConsumer per request.
pokemon_event_consumer = PokemonEventConsumer()
