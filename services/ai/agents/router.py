"""
╔══════════════════════════════════════════════════════════════════════════╗
║  NexusOS — Hybrid AI Router (with Hermes Tier)                           ║
║  File: services/ai/agents/router.py                                      ║
╠══════════════════════════════════════════════════════════════════════════╣
║  WHAT CHANGED:                                                           ║
║  Added HERMES tier — nous-hermes-3 running locally via Ollama.          ║
║  Hermes is fine-tuned specifically for agentic tool-calling and          ║
║  structured JSON output. It's dramatically better than generic           ║
║  Llama3:8b for tasks that involve reasoning about structured data.      ║
║                                                                          ║
║  THE 4-TIER MODEL STRATEGY:                                              ║
║  ┌─────────────────────────────────────────────────────────────────┐    ║
║  │  CHEAP   → Llama3:8b  $0.00  classify email, tag tickets       │    ║
║  │  HERMES  → Hermes-3   $0.00  structured reasoning, tool calls  │    ║
║  │  NORMAL  → Claude 3.5 $0.004 customer writing, SEO copy        │    ║
║  │  COMPLEX → GPT-4o     $0.015 financial analysis, contracts     │    ║
║  └─────────────────────────────────────────────────────────────────┘    ║
║                                                                          ║
║  WHY HERMES SPECIFICALLY?                                                ║
║  Nous-Hermes was fine-tuned by Nous Research on function-calling        ║
║  and structured output datasets. When a CrewAI tool needs to produce    ║
║  {"order_id": "123", "amount": 50.0} reliably, Hermes does it right    ║
║  far more often than base Llama. Zero cost — runs on Ollama.           ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os
from enum import Enum

# ── LangChain LLM connectors ───────────────────────────────────────────────────
# LangChain wraps different AI APIs behind a UNIFIED interface.
# Every LLM — whether Claude, GPT-4o, or Ollama — exposes the same method:
#   llm.invoke("your prompt") → returns a message object with .content
# This means we can swap models without changing the calling code.
from langchain_openai import ChatOpenAI       # GPT-4o via OpenAI API
from langchain_anthropic import ChatAnthropic # Claude 3.5 Sonnet via Anthropic API
from langchain_ollama import ChatOllama       # Local models via Ollama Docker container


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: Task Complexity Tiers
# ═══════════════════════════════════════════════════════════════════════════════

class TaskComplexity(str, Enum):
    """
    Defines the four tiers of AI task complexity.

    WHY str + Enum (not just strings)?
    `class TaskComplexity(str, Enum)` means each enum value IS a string.
    TaskComplexity.CHEAP == "cheap" → True
    This avoids typos ("cheep" vs "cheap") while allowing string comparisons.
    Python catches invalid enum access at import time, not silently at runtime.

    WHY 4 TIERS INSTEAD OF 2 (cheap/expensive)?
    There's a large gap between "classify an email" (5B params fine) and
    "write empathetic customer copy" (needs Claude quality). Hermes fills that
    gap for structured reasoning tasks that need more than Llama3:8b but don't
    need expensive API calls.
    """
    # Simple text understanding: classification, extraction, routing
    # Model: Ollama Llama3:8b (the generic model — good for yes/no, classify, tag)
    CHEAP = "cheap"

    # Structured reasoning, JSON output, tool-calling, agent-to-agent decisions
    # Model: Ollama Hermes-3 (fine-tuned for exactly this type of work, still free)
    HERMES = "hermes"

    # High-quality writing, nuance, empathy, marketing copy
    # Model: Claude 3.5 Sonnet (~$0.004/call — worth it for customer-facing content)
    NORMAL = "normal"

    # Multi-step financial/legal reasoning, math, large-context analysis
    # Model: GPT-4o (~$0.015/call — use only where accuracy at scale matters)
    COMPLEX = "complex"


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: Task Routing Table
# ═══════════════════════════════════════════════════════════════════════════════
#
# Maps every task type string → the optimal cost/quality tier for that task.
#
# HOW TO ADD A NEW TASK:
# Just add one line to this dict. No code changes elsewhere needed.
# The router picks it up automatically via TASK_ROUTING_TABLE.get(task_type).
#
# HOW TO CHOOSE A TIER:
# Ask yourself:
# - Does it need empathetic or creative writing? → NORMAL (Claude)
# - Does it involve numbers, legal reasoning, or long financial docs? → COMPLEX (GPT-4o)
# - Does it produce structured JSON or reason about tool calls? → HERMES
# - Is it just: read text + classify it? → CHEAP (Llama3)

TASK_ROUTING_TABLE = {

    # ── CHEAP: Ollama Llama3:8b ── (free local, ~8B params) ────────────────────
    # These tasks only need to READ and LABEL. No complex reasoning required.
    # An 8B model handles "is this a refund request or a shipping question?" fine.

    "classify_email":              TaskComplexity.CHEAP,   # Support/spam/inquiry classification
    "tag_ticket":                  TaskComplexity.CHEAP,   # Apply tags: shipping, refund, damage
    "extract_order_id":            TaskComplexity.CHEAP,   # Pull "#10234" from customer message
    "sentiment_analysis":          TaskComplexity.CHEAP,   # Angry/neutral/happy classification
    "check_spam":                  TaskComplexity.CHEAP,   # Is this message genuine or a bot?
    "basic_product_search":        TaskComplexity.CHEAP,   # Is this a card name or a question?

    # ── HERMES: Ollama Hermes-3 ── (free local, structured output specialist) ──
    # These tasks need more reasoning than Llama3 but don't need paid APIs.
    # Hermes is fine-tuned on tool-calling and structured JSON — zero hallucination
    # on structured outputs that Llama3 would often get wrong.

    "route_intent":                TaskComplexity.HERMES,  # A2A: what type of B2B query is this?
    "logistics_analysis":          TaskComplexity.HERMES,  # Evaluate supply options with numbers
    "supplier_comparison":         TaskComplexity.HERMES,  # Compare 3 suppliers: output JSON
    "inventory_summary":           TaskComplexity.HERMES,  # Structured inventory report
    "arbitrage_evaluation":        TaskComplexity.HERMES,  # Reverse market: score opportunities
    "influencer_scoring":          TaskComplexity.HERMES,  # Score influencer fit 0-100
    "storefront_context_analysis": TaskComplexity.HERMES,  # Generative UI: classify visitor intent
    "tool_call_structuring":       TaskComplexity.HERMES,  # Any task that needs reliable JSON out

    # ── NORMAL: Claude 3.5 Sonnet ── ($0.004/call via Anthropic API) ───────────
    # High-quality writing tasks. Claude is trained to be helpful, harmless, honest.
    # Its writing feels human — not robotic. Worth paying for on customer-facing content.

    "draft_customer_reply":        TaskComplexity.NORMAL,  # Support resolution emails
    "draft_refund_message":        TaskComplexity.NORMAL,  # Refund confirmation with empathy
    "marketing_copy":              TaskComplexity.NORMAL,  # Ad copy, product highlights
    "ticket_resolution":           TaskComplexity.NORMAL,  # Full agent resolution narrative
    "seo_description":             TaskComplexity.NORMAL,  # SEO product descriptions
    "cart_recovery_email":         TaskComplexity.NORMAL,  # Abandoned cart recovery emails
    "influencer_outreach":         TaskComplexity.NORMAL,  # Personalized influencer DMs
    "storefront_personalization":  TaskComplexity.NORMAL,  # Personalized page copy
    "dispute_response":            TaskComplexity.NORMAL,  # Chargeback narrative (moved here; see below)

    # ── COMPLEX: GPT-4o ── ($0.015/call via OpenAI API) ────────────────────────
    # Multi-step reasoning, math, legal/financial judgment.
    # GPT-4o's 128K token context window handles long financial docs without truncation.
    # Its reasoning training makes it reliable for calculation-heavy tasks.
    # NOTE: dispute_response originally here — moved to NORMAL since Claude handles
    #       it well and saves ~$0.011/call. Only keep truly complex reasoning here.

    "financial_analysis":          TaskComplexity.COMPLEX, # Is this PO profitable? Margin calcs
    "risk_assessment":             TaskComplexity.COMPLEX, # Full fraud score explanation
    "q3_financial_risk":           TaskComplexity.COMPLEX, # Quarterly risk report generation
    "ltv_prediction":              TaskComplexity.COMPLEX, # Customer lifetime value ML analysis
    "contract_negotiation":        TaskComplexity.COMPLEX, # B2B contract terms reasoning
    "compliance_audit":            TaskComplexity.COMPLEX, # GDPR/CCPA compliance analysis
    "bulk_arbitrage_strategy":     TaskComplexity.COMPLEX, # Multi-product market strategy
}


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: HybridAIRouter
# ═══════════════════════════════════════════════════════════════════════════════

class HybridAIRouter:
    """
    Routes AI calls to the most cost-effective appropriate model.

    DESIGN PATTERN: Lazy initialization (lazy loading).
    LLM clients are NOT created at startup. They're created on first use
    and cached thereafter. This means:
    - A service that never makes a COMPLEX call never creates a GPT-4o client
    - Startup is fast (no API validation calls)
    - Memory is only used for models actually needed in this session

    CACHING MECHANISM:
    self._llms is a dict mapping tier name → LLM instance.
    {"ollama": ChatOllama(...), "claude": ChatAnthropic(...), ...}
    Second call to _get_claude() returns the cached instance immediately.

    COMPARISON TO SIMPLE APPROACH (if model == "gpt4": ...):
    The routing table approach scales — adding a new model or new task type
    is one line. The simple approach requires modifying every caller.
    """

    def __init__(self):
        # Private cache: model tier name → LLM client instance
        # The underscore prefix is Python's convention for "private" attributes.
        # Not enforced by Python itself, but signals "don't access this from outside."
        self._llms: dict = {}

    # ── Private LLM Factory Methods ───────────────────────────────────────────
    # Each method creates the LLM client once and caches it.
    # "if not in self._llms" check = the lazy init guard.

    def _get_ollama_llama(self) -> ChatOllama:
        """
        Llama3:8b — general purpose local model for simple classification.

        WHY temperature=0.1?
        Temperature controls randomness in token selection:
          0.0 = always picks the most-likely next token (fully deterministic)
          1.0 = much more random/creative
          0.1 = very low randomness, nearly deterministic output

        For classification tasks ("is this spam?"), we want consistent answers,
        not creative variation. Low temperature = stable, predictable output.
        """
        if "llama3" not in self._llms:
            self._llms["llama3"] = ChatOllama(
                model="llama3:8b",
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=0.1,  # very low — we want consistent classifications
            )
        return self._llms["llama3"]

    def _get_hermes(self) -> ChatOllama:
        """
        Nous-Hermes-3 — local model fine-tuned for structured output & tool-calling.

        WHY HERMES FOR STRUCTURED TASKS?
        Base Llama3 will often produce invalid JSON, miss required fields, or
        hallucinate extra fields when you ask for structured output.
        Hermes-3 was specifically trained on tool-call and JSON output datasets,
        so it reliably produces valid structured responses.

        WHERE HERMES SHINES IN NEXUSOS:
        - A2A negotiation: classifying what type of B2B request it is → JSON response
        - Arbitrage agent: scoring 500 supplier opportunities → structured JSON per item
        - Logistics analysis: comparing suppliers with numbers → structured comparison

        temperature=0.1: Same reasoning as Llama — structured outputs need consistency.

        MODEL NAME IN OLLAMA:
        "hermes3" → Nous-Hermes-3. Pull command: `ollama pull hermes3`
        Also available: "nous-hermes2" (older), "hermes2-pro-mistral" (larger but slower)
        """
        if "hermes" not in self._llms:
            self._llms["hermes"] = ChatOllama(
                model="hermes3",  # Nous-Hermes-3 — pulled automatically on first use
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=0.1,  # structured output needs determinism
            )
        return self._llms["hermes"]

    def _get_claude(self) -> ChatAnthropic:
        """
        Claude 3.5 Sonnet — Anthropic's API for high-quality writing tasks.

        WHY temperature=0.3 (higher than local models)?
        Writing tasks benefit from a little creative variation:
        - Every refund email shouldn't start with the same sentence
        - SEO descriptions should feel unique, not templated
        - Cart recovery emails need a human voice

        0.3 is the sweet spot: consistent enough to follow instructions,
        varied enough to sound natural.

        max_tokens=4096:
        4096 tokens ≈ 3,000 words. Large enough for:
        - A full product SEO package (description + meta + schema ≈ 800 words)
        - A detailed chargeback dispute response (≈ 500 words)
        - A complete support ticket resolution ≈ 400 words)
        """
        if "claude" not in self._llms:
            self._llms["claude"] = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",  # pinned version prevents surprise breaking changes
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                temperature=0.3,   # some variation — writing tasks benefit from this
                max_tokens=4096,   # up to ~3000 words per response
            )
        return self._llms["claude"]

    def _get_openai(self) -> ChatOpenAI:
        """
        GPT-4o — OpenAI's premium model for complex reasoning.

        WHY temperature=0.2 (lower than Claude)?
        Financial calculations and legal reasoning must be accurate and consistent.
        A refund approval should give the same margin calculation every time.
        Low temperature = low variance = predictable outputs for critical decisions.

        WHY GPT-4o OVER GPT-4-TURBO OR o1?
        - GPT-4o: 128K context, fast, multimodal, good at structured reasoning
        - GPT-4-turbo: older, more expensive, often slower
        - o1-preview: specialized for pure chain-of-thought reasoning (great for math)
                      but slower and more expensive. Use o1 if financial calcs are wrong.
        GPT-4o is the right default for financial analysis tasks.
        """
        if "openai" not in self._llms:
            self._llms["openai"] = ChatOpenAI(
                model="gpt-4o",
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.2,   # low — financial reasoning needs consistency
            )
        return self._llms["openai"]

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_llm(self, task_type: str):
        """
        Return the optimal LLM instance for the given task type.

        ROUTING LOGIC:
        1. Look up task_type in TASK_ROUTING_TABLE → get complexity tier
        2. Return the cached (or newly created) LLM for that tier
        3. Unknown task types → NORMAL (Claude) as safe default

        FALLBACK CHAIN FOR LOCAL MODELS:
        If Hermes isn't available (not yet pulled): → fall back to Claude
        If Llama3 isn't available: → fall back to Hermes, then Claude
        We never want a missing Ollama model to break the entire service.

        Args:
            task_type: A string key from TASK_ROUTING_TABLE.
                       Unknown keys default to NORMAL (Claude) — safe default.

        Returns:
            A LangChain LLM object. All support: llm.invoke("prompt") → response
        """
        # dict.get(key, default) — returns value or default if key missing
        # Unknown tasks default to NORMAL (Claude) — better than failing
        complexity = TASK_ROUTING_TABLE.get(task_type, TaskComplexity.NORMAL)

        if complexity == TaskComplexity.CHEAP:
            try:
                llm = self._get_ollama_llama()
                print(f"[router] {task_type} → Ollama:Llama3:8b (free)")
                return llm
            except Exception as e:
                # Ollama unavailable → gracefully degrade to Hermes or Claude
                print(f"[router] Llama3 unavailable ({e}), trying Hermes")
                try:
                    return self._get_hermes()
                except Exception:
                    print(f"[router] Hermes also unavailable, falling back to Claude")
                    return self._get_claude()

        elif complexity == TaskComplexity.HERMES:
            try:
                llm = self._get_hermes()
                print(f"[router] {task_type} → Ollama:Hermes-3 (free, structured)")
                return llm
            except Exception as e:
                # Hermes not pulled yet → fall back to Claude (paid but reliable)
                print(f"[router] Hermes unavailable ({e}), falling back to Claude")
                return self._get_claude()

        elif complexity == TaskComplexity.COMPLEX:
            print(f"[router] {task_type} → GPT-4o (complex reasoning)")
            return self._get_openai()

        else:
            # TaskComplexity.NORMAL — and also the default for unknown task types
            print(f"[router] {task_type} → Claude-3.5-Sonnet (writing/standard)")
            return self._get_claude()

    def estimate_cost(self, task_type: str, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate the USD cost of a specific LLM call.

        WHAT ARE TOKENS?
        LLMs tokenize text before processing. One token ≈ 0.75 words.
        "Hello, world!" = 4 tokens. A 500-word prompt ≈ 650 tokens.
        API providers charge per 1,000,000 tokens (per-million pricing).

        WHY TRACK COSTS?
        1. The merchant dashboard shows "NexusOS cost $4.23 this month"
        2. FinanceAgent can flag if daily AI spend exceeds the $5 budget
        3. Helps optimize the routing table — if a NORMAL task is cheap enough,
           upgrade it to a better model without budget fear.

        PRICING (approximate 2026 rates):
        Ollama local:        $0.00/token (you pay server cost, not per-call)
        Claude 3.5 Sonnet:   $3.00/M input tokens, $15.00/M output tokens
        GPT-4o:              $10.00/M input tokens, $30.00/M output tokens

        EXAMPLE:
        Support email: 500 input tokens, 200 output tokens via Claude Sonnet
        Cost = (500/1M × $3.00) + (200/1M × $15.00)
             = $0.0015 + $0.003
             = $0.0045 per email

        Args:
            task_type:     Same key used in get_llm()
            input_tokens:  Tokens in the prompt you sent
            output_tokens: Tokens in the response received

        Returns:
            Cost in USD, rounded to 6 decimal places ($0.000XXX precision).
        """
        complexity = TASK_ROUTING_TABLE.get(task_type, TaskComplexity.NORMAL)

        # Pricing table: USD per 1 million tokens
        pricing = {
            TaskComplexity.CHEAP:   {"input": 0.0,  "output": 0.0},    # free (Llama3 local)
            TaskComplexity.HERMES:  {"input": 0.0,  "output": 0.0},    # free (Hermes local)
            TaskComplexity.NORMAL:  {"input": 3.0,  "output": 15.0},   # Claude 3.5 Sonnet
            TaskComplexity.COMPLEX: {"input": 10.0, "output": 30.0},   # GPT-4o
        }

        p = pricing[complexity]

        # Calculate: (tokens / 1,000,000) × price_per_million
        # Example: 500 input tokens at $3/M = (500/1000000) × 3 = $0.0015
        cost = (
            (input_tokens / 1_000_000 * p["input"])
            + (output_tokens / 1_000_000 * p["output"])
        )

        return round(cost, 6)  # 6 decimal places needed — costs can be tiny fractions of a cent
