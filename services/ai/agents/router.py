"""
╔══════════════════════════════════════════════════════════════════════════╗
║         NexusOS — Hybrid AI Router                                       ║
║         File: services/ai/agents/router.py                               ║
╠══════════════════════════════════════════════════════════════════════════╣
║  WHAT THIS FILE IS:                                                      ║
║  The "traffic controller" for AI model selection.                        ║
║  EVERY time we make an AI call in this project, it goes through here.   ║
║                                                                          ║
║  THE CORE PROBLEM IT SOLVES:                                             ║
║  AI APIs are EXPENSIVE. Using GPT-4o for every task would cost $100s/   ║
║  month on a busy store. But using a cheap model for everything makes    ║
║  the AI produce bad output for complex tasks.                           ║
║                                                                          ║
║  THE SOLUTION — 3-tier routing:                                         ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │  Task: classify email (easy)   → Ollama Llama3:8b   = $0.000    │   ║
║  │  Task: write customer reply    → Claude 3.5 Sonnet  = ~$0.004   │   ║
║  │  Task: assess financial risk   → GPT-4o             = ~$0.015   │   ║
║  └──────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
║  RESULT: ~70% cost reduction while keeping quality where it matters.    ║
║                                                                          ║
║  WHERE IT'S USED IN THE PROJECT:                                        ║
║  - agents/crew.py         → each agent picks the right model            ║
║  - agents/negotiation.py  → A2A pricing decisions                       ║
║  - routers/fraud.py       → chargeback dispute responses                ║
║  - routers/cart_recovery.py → personalized email drafting               ║
║  - routers/seo.py         → product description generation              ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# ── Standard library imports ───────────────────────────────────────────────────
import os            # os.getenv() reads environment variables from the .env file
from enum import Enum  # Enum = a set of named constants. Prevents typos like "cheep" vs "cheap"

# ── LangChain LLM connectors ───────────────────────────────────────────────────
# LangChain is a framework that wraps different AI APIs with a UNIFIED interface.
# Without LangChain: you'd have to learn OpenAI's SDK, Anthropic's SDK, Ollama's API
# separately — different method names, different response formats, etc.
# With LangChain: all three look the same: llm.invoke("your prompt") → returns text.
# The specific class (ChatOpenAI / ChatAnthropic / ChatOllama) handles the
# underlying API differences for you.

from langchain_openai import ChatOpenAI        # Wraps OpenAI's API (GPT-4o, o1-preview)
from langchain_anthropic import ChatAnthropic  # Wraps Anthropic's API (Claude 3.5 Sonnet)
from langchain_ollama import ChatOllama        # Wraps local Ollama (Llama3:8b running in Docker)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: Define Task Complexity Tiers
# ═══════════════════════════════════════════════════════════════════════════════

class TaskComplexity(str, Enum):
    """
    The three tiers of task complexity. Each tier maps to a different model.

    WHY USE Enum INSTEAD OF JUST STRINGS?
    If we used plain strings ("cheap", "normal", "complex"), a typo anywhere
    would silently route the task to the wrong model. With an Enum:
      TaskComplexity.CHEAP     ← Python will catch typos at import time
      TaskComplexity.CHEAP == "cheap"  ← True (we inherit from str, so comparisons work)

    WHY INHERIT FROM str?
    `class TaskComplexity(str, Enum)` means the enum VALUES are also regular strings.
    So TaskComplexity.CHEAP == "cheap" evaluates to True.
    This lets us use them in string comparisons and JSON serialization without
    calling .value everywhere. It's a Python convenience pattern.
    """
    # CHEAP: Tasks that only require basic text understanding.
    # Examples: "Is this email a support request or spam?" = just classify the intent.
    # A free, locally-running 8B parameter model can do this well.
    CHEAP = "cheap"

    # NORMAL: Tasks that need fluent writing or moderate reasoning.
    # Examples: "Write a empathetic refund email" — needs good English and tact.
    # Claude 3.5 Sonnet excels at writing. ~$0.004 per call.
    NORMAL = "normal"

    # COMPLEX: Tasks requiring deep reasoning about numbers, risk, or implications.
    # Examples: "Assess financial risk of this purchase order" — GPT-4o's large
    # context window and reasoning ability shine here. ~$0.015 per call.
    COMPLEX = "complex"


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: Routing Table — Maps task names to complexity tiers
# ═══════════════════════════════════════════════════════════════════════════════

# This is a Python dictionary (dict): {key: value, key: value, ...}
# Key   = task name (a string describing what we're doing)
# Value = TaskComplexity ENUM value (which tier that task belongs to)
#
# HOW IT'S USED:
#   task_name = "classify_email"
#   complexity = TASK_ROUTING_TABLE.get(task_name)  → TaskComplexity.CHEAP
#   router picks Ollama (free local model)
#
# ADDING A NEW TASK: Just add a new line here. The router picks it up automatically.

TASK_ROUTING_TABLE = {

    # ── CHEAP: Ollama Llama3:8b — runs locally, costs $0 ──────────────────
    # These tasks just need to READ and CLASSIFY text.
    # An 8 billion parameter model is more than capable enough.
    # If you're spending money on GPT-4o to classify emails, you're burning cash.

    "classify_email":     TaskComplexity.CHEAP,  # Determine if email = support/spam/inquiry
    "tag_ticket":         TaskComplexity.CHEAP,  # Apply tags: "shipping", "refund", "damage"
    "extract_order_id":   TaskComplexity.CHEAP,  # Pull "order #5001234" from customer text
    "sentiment_analysis": TaskComplexity.CHEAP,  # Is the customer angry, neutral, or happy?
    "route_intent":       TaskComplexity.CHEAP,  # Used in A2A: what type of B2B query is this?
    "check_spam":         TaskComplexity.CHEAP,  # Is this message genuine or a bot?

    # ── NORMAL: Claude 3.5 Sonnet — API call, ~$0.004 ────────────────────
    # These tasks need QUALITY WRITING — empathy, clarity, brand voice.
    # Ollama's writing feels robotic. Claude produces output indistinguishable
    # from a skilled human writer. Worth the extra cost.

    "draft_customer_reply":  TaskComplexity.NORMAL,  # "Dear Alex, I understand your frustration..."
    "draft_refund_message":  TaskComplexity.NORMAL,  # Refund confirmation email with empathy
    "logistics_analysis":    TaskComplexity.NORMAL,  # Evaluate supply disruption options
    "supplier_comparison":   TaskComplexity.NORMAL,  # Compare 3 suppliers by price/lead time
    "marketing_copy":        TaskComplexity.NORMAL,  # Ad copy, product highlights
    "inventory_summary":     TaskComplexity.NORMAL,  # "Your Q3 inventory at a glance..."
    "ticket_resolution":     TaskComplexity.NORMAL,  # Full ticket resolution narrative

    # ── COMPLEX: GPT-4o — API call, ~$0.015 ──────────────────────────────
    # These tasks require multi-step reasoning, math, or legal/financial judgment.
    # GPT-4o's large context window (128K tokens) handles long financial reports.
    # Its "o1-preview" variant specializes in step-by-step reasoning.

    "financial_analysis":   TaskComplexity.COMPLEX,  # Is this PO profitable after fees?
    "risk_assessment":      TaskComplexity.COMPLEX,  # Fraud risk score analysis + explanation
    "q3_financial_risk":    TaskComplexity.COMPLEX,  # Quarterly risk report generation
    "ltv_prediction":       TaskComplexity.COMPLEX,  # Customer lifetime value forecasting
    "contract_negotiation": TaskComplexity.COMPLEX,  # B2B contract terms reasoning
    "compliance_audit":     TaskComplexity.COMPLEX,  # GDPR/CCPA compliance review
}


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: HybridAIRouter Class
# ═══════════════════════════════════════════════════════════════════════════════

class HybridAIRouter:
    """
    Routes AI calls to the most cost-effective model for the task.

    DESIGN PATTERN: Lazy initialization (also called lazy loading).
    We don't create the LLM clients at startup. We create them the FIRST TIME
    they're needed and cache them for reuse.

    WHY LAZY INIT?
    Creating a ChatOpenAI instance makes an API call to validate your key.
    If we created all three at startup, every service restart would make 3 API
    calls — even if this service never uses GPT-4o that session.
    Lazy init only creates the client when (and if) it's actually needed.

    HOW CACHING WORKS:
    We store created LLM instances in self._llms dict.
    First call to _get_claude(): creates ChatAnthropic, stores in self._llms["claude"]
    Second call:                 finds "claude" in self._llms, returns cached instance
    This avoids creating a new HTTP client on every AI call (expensive overhead).
    """

    def __init__(self):
        # Private dict to cache LLM instances.
        # The underscore prefix `_llms` is Python's convention for "private".
        # It's not enforced by Python, but signals to other developers:
        # "don't access this directly; use the public methods instead."
        self._llms = {}

    # ── Private LLM Factory Methods ───────────────────────────────────────────

    def _get_ollama(self) -> ChatOllama:
        """
        Create or return cached Ollama (local Llama3) client.

        WHAT IS OLLAMA?
        Ollama runs open-source AI models locally on your machine (or server).
        No API key needed. No per-call cost. The model runs in the Docker container
        defined in docker-compose.yml (image: ollama/ollama:latest).

        WHAT IS LLAMA3:8B?
        Meta's Llama 3 model with 8 BILLION parameters.
        "Parameters" = the learned weights in the neural network.
        8B is large enough for classification tasks but small enough
        to run on a machine with 8GB+ RAM (no GPU required for inference).

        temperature=0.1 means VERY LOW RANDOMNESS.
        Temperature 0 = always picks the most likely next token (deterministic).
        Temperature 1 = more creative/random.
        For classification, we want consistent, predictable output → low temp.
        """
        # `if "ollama" not in self._llms` → only create once, reuse after that
        if "ollama" not in self._llms:
            self._llms["ollama"] = ChatOllama(
                model="llama3:8b",
                # OLLAMA_BASE_URL env var: where is the Ollama Docker container?
                # "http://localhost:11434" if running locally
                # "http://ollama:11434" if running inside Docker Compose network
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=0.1,  # low randomness for classification tasks
            )
        return self._llms["ollama"]  # return cached instance

    def _get_claude(self) -> ChatAnthropic:
        """
        Create or return cached Claude 3.5 Sonnet client.

        WHY CLAUDE FOR WRITING?
        Anthropic trained Claude with emphasis on:
        - Helpfulness: follows instructions precisely
        - Harmlessness: won't write misleading content
        - Honesty: acknowledges uncertainty instead of hallucinating

        For customer emails and marketing copy, Claude's writing quality
        is consistently better than GPT-3.5 and comparable to GPT-4o
        at 1/4 the price.

        temperature=0.3: slightly higher than Ollama (0.1) because writing
        tasks benefit from some creative variation. We don't want every
        refund email to start with identically the same sentence.

        max_tokens=4096: maximum length of the response. 4096 tokens ≈ 3,000 words.
        Product descriptions, recovery emails, dispute responses all fit.
        """
        if "claude" not in self._llms:
            self._llms["claude"] = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",  # exact model version pinned
                api_key=os.getenv("ANTHROPIC_API_KEY"),  # reads from .env file
                temperature=0.3,
                max_tokens=4096,
            )
        return self._llms["claude"]

    def _get_openai(self) -> ChatOpenAI:
        """
        Create or return cached GPT-4o client.

        WHY GPT-4O FOR COMPLEX TASKS?
        GPT-4o (Omni) has:
        - 128K token context window (can read entire financial reports)
        - Strong structured reasoning (calculates margins correctly)
        - Reliable JSON output (critical for fraud score responses)
        - Training on more financial/legal documents than Claude

        temperature=0.2: very low, since financial analysis must be accurate
        and consistent. We don't want randomness affecting whether a $335
        purchase order gets approved or rejected.
        """
        if "openai" not in self._llms:
            self._llms["openai"] = ChatOpenAI(
                model="gpt-4o",
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.2,  # low randomness for factual financial reasoning
            )
        return self._llms["openai"]

    # ── Public API ────────────────────────────────────────────────────────────

    def get_llm(self, task_type: str):
        """
        The main public method. Returns the correct LLM for the given task.

        HOW IT WORKS:
        1. Look up task_type in TASK_ROUTING_TABLE → get complexity tier
        2. If complexity == CHEAP  → try Ollama first, fall back to Claude if Ollama is down
        3. If complexity == COMPLEX → return GPT-4o
        4. If complexity == NORMAL (or unknown task_type) → return Claude

        Args:
            task_type: A string key from TASK_ROUTING_TABLE.
                       Unknown task types default to NORMAL (Claude).
                       This is the "safe default" — better to over-spend slightly
                       than to get bad output from Ollama on an unknown task.

        Returns:
            A LangChain LLM object. All of them support .invoke("prompt") → response.
        """
        # dict.get(key, default) → returns the value for key, or default if key not found.
        # Unknown task types default to NORMAL (Claude). Better safe than sorry.
        complexity = TASK_ROUTING_TABLE.get(task_type, TaskComplexity.NORMAL)

        if complexity == TaskComplexity.CHEAP:
            try:
                # Try Ollama first (free, local). If Ollama's Docker container is
                # not running, _get_ollama() itself won't fail — the failure happens
                # when we actually call .invoke() on it. So we wrap in try/except
                # at the usage level, not here.
                # The try/except here handles the case where Ollama can't even be
                # initialized (e.g., wrong base_url causing immediate socket error).
                llm = self._get_ollama()
                print(f"[router] {task_type} → Ollama:Llama3:8b (free)")
                return llm
            except Exception as e:
                # Ollama connection failed → degrade gracefully to Claude.
                # This means the system still works even if local Ollama is down.
                # We just pay a bit more for that call.
                # This is called "graceful degradation" — fail to the next best option.
                print(f"[router] Ollama unavailable ({e}), falling back to Claude")
                return self._get_claude()

        elif complexity == TaskComplexity.COMPLEX:
            print(f"[router] {task_type} → GPT-4o (complex reasoning)")
            return self._get_openai()

        else:
            # TaskComplexity.NORMAL is the else branch.
            # ANY unknown task also falls here (due to the .get() default above).
            print(f"[router] {task_type} → Claude-3.5-Sonnet (standard)")
            return self._get_claude()

    def estimate_cost(self, task_type: str, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate the monetary cost in USD for a specific task call.

        WHAT ARE TOKENS?
        LLMs don't process words — they process "tokens" (roughly 3/4 of a word).
        "Hello world" = 2 tokens. A 300-word email prompt ≈ 400 tokens.
        API providers charge per 1,000 or 1,000,000 tokens.

        THIS IS HOW API PRICING WORKS (2026 approximate rates):
          Ollama:          $0.000 (you pay for the server, not per-call)
          Claude 3.5 Sonnet: $3.00/1M input tokens, $15.00/1M output tokens
          GPT-4o:          $10.00/1M input tokens, $30.00/1M output tokens

        HOW TO USE THIS:
          cost = router.estimate_cost("draft_customer_reply", input_tokens=500, output_tokens=200)
          # → cost = (500/1M × $3.00) + (200/1M × $15.00)
          # →      = $0.0015 + $0.003 = $0.0045 per email draft

        WHY TRACK COSTS?
        So the merchant dashboard can show: "This month, NexusOS made 1,247
        AI calls for a total cost of $4.23." Transparency builds trust.

        Args:
            task_type: Same task_type string used in get_llm()
            input_tokens: How many tokens were in the prompt
            output_tokens: How many tokens were in the response

        Returns:
            Cost in USD as a float, rounded to 6 decimal places.
        """
        complexity = TASK_ROUTING_TABLE.get(task_type, TaskComplexity.NORMAL)

        # Pricing lookup table. Units: USD per 1 MILLION tokens.
        # /1_000_000 in the calculation converts from "per million" to "per token".
        pricing = {
            TaskComplexity.CHEAP:   {"input": 0.0,   "output": 0.0},     # free (local)
            TaskComplexity.NORMAL:  {"input": 3.0,   "output": 15.0},    # Claude 3.5 Sonnet
            TaskComplexity.COMPLEX: {"input": 10.0,  "output": 30.0},    # GPT-4o
        }

        p = pricing[complexity]

        # Cost formula:
        #   input_cost  = (input_tokens  ÷ 1,000,000) × price_per_million_input_tokens
        #   output_cost = (output_tokens ÷ 1,000,000) × price_per_million_output_tokens
        #   total_cost  = input_cost + output_cost
        cost = (input_tokens / 1_000_000 * p["input"]) + (output_tokens / 1_000_000 * p["output"])

        # round(x, 6) → 6 decimal places. Cost can be tiny fractions of a cent.
        # Example: 0.001234 USD = $0.001234 per call
        return round(cost, 6)
