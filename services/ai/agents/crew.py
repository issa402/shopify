"""
╔══════════════════════════════════════════════════════════════════════════╗
║  NexusOS — CrewAI Multi-Agent Swarm                                      ║
║  File: services/ai/agents/crew.py                                        ║
╠══════════════════════════════════════════════════════════════════════════╣
║  WHAT THIS FILE IS:                                                      ║
║  Defines the THREE AI agents that form the NexusOS operations team,     ║
║  their tools, goals, and how they collaborate.                           ║
║                                                                          ║
║  WHAT IS CREWAI?                                                         ║
║  CrewAI is a Python framework for building TEAMS of AI agents.          ║
║  Instead of one AI doing everything (which confuses it), CrewAI lets you║
║  define specialized agents — each with a specific role, backstory,       ║
║  set of tools, and the exact model it should use.                       ║
║                                                                          ║
║  THINK OF IT LIKE A COMPANY:                                            ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │  CEO (FinanceAgent)  ← approves money decisions                  │   ║
║  │    ↕ delegation                                                   │   ║
║  │  Customer Service (SupportAgent) ← handles tickets               │   ║
║  │  Logistics Manager (LogisticsAgent) ← handles inventory/supply   │   ║
║  └──────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
║  HIERARCHICAL PROCESS:                                                   ║
║  FinanceAgent = manager. Any action >$100 must get its approval.        ║
║  Support or Logistics can't spend money without Finance saying yes.      ║
║                                                                          ║
║  WHERE IT GETS CALLED:                                                   ║
║  routers/agents.py → POST /agents/support/resolve                       ║
║  routers/agents.py → POST /agents/logistics/disruption                  ║
║  consumers/pokemon_events.py → when a deal/trend arrives from Kafka     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os   # for reading environment variables

# ── CrewAI imports ─────────────────────────────────────────────────────────────
# Agent: defines one AI team member (role, goal, backstory, tools, LLM)
# Task:  defines a specific job the agent needs to complete (description + expected output)
# Crew:  the team — combines agents and a process for how they work together
# Process: how the crew operates — Process.hierarchical means manager-led
from crewai import Agent, Task, Crew, Process

# BaseTool: the base class for creating custom tools that agents can use.
# Tools are functions the AI can CALL during its reasoning process.
# Example: instead of just TALKING about checking inventory, the agent
# can actually CALL CheckInventoryTool() and get a real answer from the DB.
from crewai.tools import BaseTool

# LangChain LLM clients — same as in router.py
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama

# Our custom router that picks the right model per task
from agents.router import HybridAIRouter

from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: Tool Definitions
# ═══════════════════════════════════════════════════════════════════════════════
#
# WHAT ARE TOOLS IN CREWAI?
# When a CrewAI agent needs to do something in the REAL WORLD (check a database,
# issue a refund, send a Slack message), it calls a Tool.
#
# HOW TOOLS WORK:
# The LLM "sees" a list of available tools (their name + description).
# When it decides to use one, it outputs something like:
#   ACTION: shopify_refund
#   INPUT: {"order_id": "5001234", "amount": 50.00, "reason": "item damaged"}
# CrewAI parses this, calls the tool's _run() method with those arguments,
# then feeds the result BACK into the LLM's context so it can continue reasoning.
#
# This "action → observation → continue" loop is called ReAct (Reasoning + Acting).
# It's how agents take real-world actions without a human clicking buttons.
#
# NOTE: Most tools here have TODO comments because in production they'd call
# real APIs (Shopify Admin API, PostgreSQL via MCP, Slack API). The stubs
# let us test the agent logic without real credentials.

class ShopifyRefundTool(BaseTool):
    """
    Tool: Issue a refund on Shopify.

    HOW INHERITANCE WORKS HERE:
    `class ShopifyRefundTool(BaseTool)` means ShopifyRefundTool INHERITS from BaseTool.
    BaseTool defines the interface (name, description, _run method).
    We provide the specific values: our tool's name, what it does (description),
    and the actual code that runs (_run method).

    HOW THE AGENT USES THIS:
    The agent sees:
      Tool name: "shopify_refund"
      Description: "Issue a refund for a Shopify order. Input: {order_id, amount, reason}"
    When the agent decides a refund is appropriate, it calls this tool.
    """
    # name and description are TYPE ANNOTATED as `str`.
    # This is Pydantic syntax (CrewAI uses Pydantic under the hood).
    # `name: str = "shopify_refund"` means: attribute 'name', type: str, default: "shopify_refund"
    name: str = "shopify_refund"
    description: str = "Issue a refund for a Shopify order. Input: {order_id, amount, reason}"

    def _run(self, order_id: str, amount: float, reason: str) -> str:
        """
        The actual code that runs when the agent calls this tool.

        HUMAN-IN-THE-LOOP for large refunds:
        If amount > $100, we DON'T issue the refund automatically.
        Instead, we return a special string "APPROVAL_REQUIRED: ..."
        The agent reads this and routes the request to FinanceAgent.
        This is the Human-in-the-Loop safety mechanism — no big money moves
        happen without a human reviewing it first.

        In production:
          import shopify  # Shopify Python SDK
          transaction = shopify.Transaction.create({...})
          → This would actually create the refund in Shopify's system.
        """
        # TODO: call Shopify Admin API
        # POST https://your-store.myshopify.com/admin/api/2024-01/orders/{order_id}/refunds.json
        # Headers: {"X-Shopify-Access-Token": merchant_access_token}
        # Body: {"refund": {"transactions": [{"kind": "refund", "amount": amount}]}}

        # Safety check: amounts over $100 require FinanceAgent to approve
        if amount > 100:
            # Return a structured string that the agent framework understands as
            # "escalate this to the manager before proceeding"
            return f"APPROVAL_REQUIRED: Refund of ${amount} for order {order_id} requires manager approval."

        # Under $100: fine to issue immediately
        return f"Refund of ${amount} issued for order {order_id}. Reason: {reason}"


class CheckInventoryTool(BaseTool):
    """
    Tool: Check the current stock level for a Shopify product.

    Used by LogisticsAgent to answer questions like:
    "Do we have enough Charizard cards to fulfill this B2B order?"

    In production: Query PostgreSQL inventory_levels table
    via the MCP-Postgres connector (read-only database access for agents).
    """
    name: str = "check_inventory"
    description: str = "Check current inventory for a product. Input: {product_id}"

    def _run(self, product_id: str) -> str:
        """
        Returns current stock level and the reorder threshold.

        The "reorder point" is the level at which we should ORDER MORE stock.
        Calculated by InventoryForecaster in inventory/forecast.py
        (daily_demand × lead_time_days + safety_stock_days).

        For now, returns a realistic stub answer. In production:
          SELECT current_quantity, reorder_point FROM inventory_levels
          WHERE shopify_product_id = product_id AND merchant_id = current_merchant_id
        """
        # TODO: query inventory_levels table in PostgreSQL via MCP-Postgres
        return f"Product {product_id}: 145 units in stock, reorder point at 50 units."


class ProfitCalculatorTool(BaseTool):
    """
    Tool: Calculate profit margin impact of a refund or discount.

    Used by FinanceAgent when deciding whether to approve a refund.
    The agent needs to know: "If I approve this $50 refund, does it
    drop our margin below the 15% minimum? If yes, should we counter-offer
    with a store credit instead of a cash refund?"

    In production: Look up the order's COGS (Cost of Goods Sold) from Postgres
    and calculate: (revenue - COGS - refund_amount) / revenue × 100 = new margin %
    """
    name: str = "profit_calculator"
    description: str = "Calculate profit margin impact of a refund or discount. Input: {order_id, discount_amount}"

    def _run(self, order_id: str, discount_amount: float) -> str:
        """
        Returns the current margin and what the margin would be after the refund.

        The magic threshold is 20%: FinanceAgent's goal says "never approve
        actions that reduce margins below 15%." The calculation here gives
        Finance the data it needs to make that call.
        """
        # TODO: query order COGS from Postgres:
        # SELECT subtotal_price, line_items FROM orders WHERE id = order_id
        # Then calculate actual margin and post-refund margin
        return (
            f"Order {order_id}: Current margin 35%. "
            f"Refunding ${discount_amount} reduces margin to 28%. "
            f"WITHIN acceptable range (>20%)."
        )


class SlackNotifyTool(BaseTool):
    """
    Tool: Send a Slack message to the merchant's ops channel.

    This is how the agent team "talks" to the human merchant.
    When LogisticsAgent finds a critical supply disruption, it doesn't
    wait for the merchant to log in and check the dashboard — it sends
    a Slack message immediately.

    In production: Call MCP-Slack connector:
    POST to Slack's incoming webhook URL with {channel, text, blocks}
    """
    name: str = "slack_notify"
    description: str = "Send a Slack message to the merchant's ops channel. Input: {channel, message}"

    def _run(self, channel: str, message: str) -> str:
        # TODO: call MCP-Slack connector
        # POST https://hooks.slack.com/services/WEBHOOK_URL
        # Body: {"channel": channel, "text": message}
        return f"Slack notification sent to #{channel}: {message}"


class FindAlternativeSupplierTool(BaseTool):
    """
    Tool: Find alternative suppliers for a product.

    Used when LogisticsAgent detects that the primary supplier has a problem
    (stockout, shipping delay, quality issue). Instead of just alerting the
    merchant "your supplier is delayed" (useless), the agent proactively finds
    alternatives and compares prices/lead times.

    In production: Connect to supplier catalog database or ERP system
    (like Odoo) via MCP to run supplier search queries.
    """
    name: str = "find_alternative_supplier"
    description: str = (
        "Search for alternative suppliers for a product. "
        "Input: {product_name, quantity, max_lead_days}"
    )

    def _run(self, product_name: str, quantity: int, max_lead_days: int) -> str:
        # TODO: integrate with supplier DB or ERP via MCP
        return (
            f"Found 3 alternative suppliers for {product_name} "
            f"({quantity} units, ≤{max_lead_days} days lead time). "
            f"Best: GlobalParts Co. at $8.50/unit."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: Agent Definitions
# ═══════════════════════════════════════════════════════════════════════════════

def create_swarm(merchant_id: str) -> Crew:
    """
    Create the complete NexusOS Agent Swarm for a given merchant.

    WHY PASS merchant_id?
    When the swarm is making decisions (checking inventory, looking up orders),
    it needs the merchant_id to query the right data from PostgreSQL
    (Row-Level Security ensures agents only see that merchant's data).

    WHY CREATE A NEW CREW EACH TIME vs. having one global crew?
    Each agent call may be for a different merchant. Crew memory (embeddings)
    is per-crew. Creating per-request crews ensures memory isolation between
    merchants. Performance cost is minimal — agents are stateless objects.

    Args:
        merchant_id: The Postgres UUID of the Shopify merchant.

    Returns:
        A CrewAI Crew instance ready to kickoff() with a task.
    """
    # Create a router instance to get the right LLM for each agent
    router = HybridAIRouter()

    # ── Agent 1: SupportAgent ──────────────────────────────────────────────────
    # Role:       Customer-facing problem resolver
    # LLM:        Claude 3.5 Sonnet (needs empathetic, natural writing)
    # Tools:      ShopifyRefundTool (can issue refunds), SlackNotifyTool (can alert merchant)
    # Delegation: True (can ask FinanceAgent to approve big refunds)
    support_agent = Agent(
        # role: what this agent IS (displayed in CrewAI logs)
        role="Customer Support Specialist",

        # goal: what the agent is TRYING TO DO.
        # This is injected into every prompt the agent makes.
        # It shapes ALL of the agent's reasoning — it's like giving it a job description.
        goal=(
            "Resolve customer support tickets efficiently and empathetically. "
            "Always prioritize customer satisfaction while protecting the merchant's interests. "
            "For refunds under $100, resolve immediately. For refunds over $100, consult FinanceAgent."
        ),

        # backstory: the agent's PERSONA and EXPERIENCE.
        # This also gets injected into all prompts. It makes the agent sound
        # like a knowledgeable expert rather than a generic chatbot.
        # "You are an expert..." framing consistently improves output quality.
        backstory=(
            "You are an expert customer support agent for an e-commerce merchant. "
            "You have deep knowledge of Shopify orders, refund policies, and shipping issues. "
            "You communicate clearly and empathetically, always finding the best resolution."
        ),

        # tools: the real-world actions this agent can take.
        # Each tool instance is passed as an object. CrewAI handles calling _run().
        tools=[ShopifyRefundTool(), SlackNotifyTool()],

        # llm: which AI model powers this agent's reasoning.
        # "draft_customer_reply" → TaskComplexity.NORMAL → Claude 3.5 Sonnet
        llm=router.get_llm("draft_customer_reply"),

        # verbose=True: print all agent reasoning steps to the console.
        # Useful for debugging: you can see exactly how the agent reasoned.
        # In production: set to False to reduce log noise (optional).
        verbose=True,

        # allow_delegation=True: this agent CAN ask other agents for help.
        # When SupportAgent needs FinanceAgent's approval, it delegates.
        # This is how the hierarchical process works in practice.
        allow_delegation=True,

        # max_iter=5: the agent can go through a maximum of 5 reasoning cycles.
        # (Think → Act → Observe → Think → Act → ...)
        # Without a limit, a confused agent could loop forever burning API credits.
        max_iter=5,
    )

    # ── Agent 2: LogisticsAgent ────────────────────────────────────────────────
    # Role:       Supply chain and inventory manager
    # LLM:        Claude 3.5 Sonnet (needs analytical writing + reasoning)
    # Tools:      CheckInventoryTool, FindAlternativeSupplierTool, SlackNotifyTool
    # Delegation: False (logistics decisions don't require Finance micro-approval)
    logistics_agent = Agent(
        role="Logistics & Supply Chain Manager",
        goal=(
            "Optimize inventory levels, prevent stockouts, and maintain supplier relationships. "
            "Monitor shipping delays and proactively find alternative sources when supply chain issues arise."
        ),
        backstory=(
            "You are a seasoned supply chain expert who monitors inventory in real-time. "
            "You have relationships with multiple suppliers and can quickly find alternatives. "
            "You proactively prevent problems before they impact the merchant's sales."
        ),
        tools=[CheckInventoryTool(), FindAlternativeSupplierTool(), SlackNotifyTool()],
        # "logistics_analysis" → TaskComplexity.NORMAL → Claude 3.5 Sonnet
        llm=router.get_llm("logistics_analysis"),
        verbose=True,
        # allow_delegation=False: Logistics doesn't delegate to others.
        # It does its own analysis and reports results up to Finance for approval.
        allow_delegation=False,
        max_iter=5,
    )

    # ── Agent 3: FinanceAgent (Manager) ───────────────────────────────────────
    # Role:       Financial controller AND crew manager
    # LLM:        GPT-4o (needs precise financial reasoning + math)
    # Tools:      ProfitCalculatorTool (calculates margin impact)
    # Delegation: False (the manager doesn't delegate — it decides)
    # max_iter=3: Finance decisions should be reached in fewer steps (direct reasoning)
    finance_agent = Agent(
        role="Financial Controller & Approvals Manager",
        goal=(
            "Protect the merchant's profit margins. Review and approve/reject all financial decisions "
            "over $100, including refunds, discounts, and purchase orders. "
            "Never approve actions that would reduce margins below 15%."
        ),
        backstory=(
            "You are a detail-oriented financial controller who ensures every dollar is accounted for. "
            "You analyze the full cost impact of refunds and discounts before approval. "
            "You are strict but fair, always balancing customer satisfaction with business health."
        ),
        tools=[ProfitCalculatorTool()],
        # "financial_analysis" → TaskComplexity.COMPLEX → GPT-4o
        # We use the most capable model here because financial math errors cost money.
        llm=router.get_llm("financial_analysis"),
        verbose=True,
        allow_delegation=False,
        max_iter=3,  # Finance should decide quickly — 3 reasoning cycles is enough
    )

    # ── Assemble the Crew ──────────────────────────────────────────────────────
    return Crew(
        # List of agents in this crew. Order matters for Process.hierarchical:
        # the manager_agent is listed first by convention (though it's set explicitly below).
        agents=[finance_agent, support_agent, logistics_agent],

        # Process.hierarchical: The manager_agent oversees all task assignment.
        # It decides which agent does what, reviews outputs, and approves final actions.
        # Other option: Process.sequential (agents run tasks in order, no manager).
        # Hierarchical is better for our use case because Finance needs to review
        # any action that costs money before it's executed.
        process=Process.hierarchical,

        # manager_agent: explicitly sets FinanceAgent as the team manager.
        # With Process.hierarchical, CrewAI routes task delegation through this agent.
        manager_agent=finance_agent,

        verbose=True,

        # memory=True: the crew maintains SHARED MEMORY across tasks within one session.
        # If SupportAgent learns "the customer is angry about a shipping delay",
        # FinanceAgent knows this context when deciding whether to approve a refund.
        # Memory is stored as embeddings using the embedder config below.
        memory=True,

        # embedder: which embedding model to use for crew memory.
        # "text-embedding-3-small" from OpenAI converts text to 1536-dimension vectors.
        # These vectors are stored and searched when agents need to recall past context.
        embedder={
            "provider": "openai",
            "config": {"model": "text-embedding-3-small"},
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: Task Runner Functions
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_support_ticket(crew: Crew, ticket: dict) -> str:
    """
    Run the agent swarm on a specific customer support ticket.

    WHAT IS A TASK?
    A Task tells the crew EXACTLY what to do this time.
    Think of it as an assignment memo handed to the agents.
    It has:
      - description: detailed instructions (what the issue is, what steps to follow)
      - expected_output: what format we want the answer in
      - agent: which agent STARTS the task (the SupportAgent)
                The manager can reassign if needed.

    Args:
        crew: The Crew instance created by create_swarm()
        ticket: Dict with keys: customer_name, order_id, issue, requested_resolution

    Returns:
        String with the full resolution (action taken + customer response drafted)
    """
    task = Task(
        description=f"""
        Resolve the following customer support ticket:

        Customer: {ticket.get('customer_name')}
        Order ID: {ticket.get('order_id')}
        Issue: {ticket.get('issue')}
        Requested Resolution: {ticket.get('requested_resolution')}

        Steps:
        1. Analyze the issue and determine the appropriate resolution
        2. If a refund >$100 is needed, get FinanceAgent approval first
        3. Take the approved action (issue refund, send replacement, generate discount code)
        4. Draft a clear, empathetic response to the customer
        5. Log the resolution for merchant review in the Approvals dashboard
        """,
        # expected_output tells the agent what format/content the result should have.
        # The agent uses this to know when it's done.
        expected_output=(
            "A structured resolution including: action taken, customer response drafted, "
            "and approval status (auto-approved or pending Finance review)"
        ),
        # The SupportAgent leads this task. If it needs Finance approval,
        # it delegates via the hierarchical process.
        agent=support_agent,  
        # Note: support_agent is defined inside create_swarm() above.
        # In production code, we'd reference it differently; this is simplified for clarity.
    )
    # crew.kickoff() starts the crew running on this task.
    # It blocks until the task completes (or max_iter is reached).
    # Returns a CrewOutput object; str() converts it to the text result.
    result = crew.kickoff(inputs={"ticket": ticket})
    return str(result)


def handle_supply_disruption(crew: Crew, disruption: dict) -> str:
    """
    Run the agent swarm to respond to a supply chain disruption.

    WHEN IS THIS CALLED?
    - LogisticsAgent detects that current_stock < reorder_point (from forecast.py)
    - A supplier sends a delay notification (via webhook)
    - Manual trigger from the Workflows UI

    Args:
        crew: The Crew instance
        disruption: Dict with keys: product_name, supplier, delay_days,
                    current_stock, daily_sales

    Returns:
        Full disruption response: alternative supplier found, emergency PO drafted,
        Slack alert sent, finance approval status.
    """
    task = Task(
        description=f"""
        A supply chain disruption has been detected:

        Product: {disruption.get('product_name')}
        Supplier: {disruption.get('supplier')}
        Expected Delay: {disruption.get('delay_days')} days
        Current Stock: {disruption.get('current_stock')} units
        Daily Sales Rate: {disruption.get('daily_sales')} units/day

        Steps:
        1. Calculate how many days of stock remain (current_stock ÷ daily_sales)
        2. Find alternative suppliers using the find_alternative_supplier tool
        3. Get Finance approval for emergency purchase if needed
        4. Alert the merchant via Slack (#ops-alerts channel)
        5. Create a draft purchase order for merchant one-click approval
        """,
        expected_output=(
            "A disruption response plan with: "
            "days of stock remaining, alternative supplier details, "
            "cost comparison, recommended action, and emergency PO draft"
        ),
        agent=logistics_agent,
    )
    result = crew.kickoff(inputs={"disruption": disruption})
    return str(result)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: Convenience Wrappers for Pokemon Kafka Consumer
# ═══════════════════════════════════════════════════════════════════════════════
#
# These are simple wrappers that consumers/pokemon_events.py uses to run agents
# without needing to know the full CrewAI setup internals.
# They create a fresh crew for each call (merchant_id="system" for internal tasks).

def run_logistics_agent(task: str) -> str:
    """
    Simple wrapper: run LogisticsAgent on a plain-text task description.

    Used by pokemon_events.py _handle_deal() to evaluate whether we should
    purchase a card listing that PokémonTool flagged as a deal.

    Args:
        task: Plain text description of what to analyze.
              e.g. "Evaluate purchase: Charizard at $320, market $450, 28.9% below"
    """
    # We use merchant_id="system" for internal automated tasks
    # (not triggered by a human merchant session).
    crew = create_swarm(merchant_id="system")

    crewai_task = Task(
        description=task,
        expected_output="Clear recommendation: BUY or SKIP. If BUY, include estimated units and reasoning.",
        agent=None,  # Let the manager decide which agent handles it
    )
    result = crew.kickoff(inputs={"task": task})
    return str(result)


def run_finance_agent(task: str) -> str:
    """
    Simple wrapper: run FinanceAgent on a plain-text task description.

    Used by pokemon_events.py to get financial approval for:
    - Deal purchases (is the 25% margin acceptable?)
    - Repricing decisions (is increasing our Shopify price justified by the market move?)

    Args:
        task: Plain text description of the financial decision to evaluate.
    """
    crew = create_swarm(merchant_id="system")

    crewai_task = Task(
        description=task,
        expected_output=(
            "Financial decision: APPROVED or REJECTED. "
            "If APPROVED: include unit cost, selling price, projected margin. "
            "If REJECTED: explain why (margin too low, budget exceeded, etc.)"
        ),
        agent=None,  # FinanceAgent is the manager so it handles financial tasks by default
    )
    result = crew.kickoff(inputs={"task": task})
    return str(result)
