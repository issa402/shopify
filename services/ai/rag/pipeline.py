"""
╔══════════════════════════════════════════════════════════════════════════╗
║  NexusOS — RAG Pipeline (Retrieval-Augmented Generation)                 ║
║  File: services/ai/rag/pipeline.py                                       ║
╠══════════════════════════════════════════════════════════════════════════╣
║  WHAT IS RAG?                                                            ║
║  RAG = Retrieval-Augmented Generation.                                   ║
║                                                                          ║
║  The PROBLEM with vanilla AI:                                            ║
║  LLMs are trained on general internet data. They don't know:            ║
║  - Your specific return policy                                           ║
║  - How you resolved similar tickets before                              ║
║  - Your product specifications                                           ║
║  So when SupportAgent tries to resolve "Package arrived damaged — want  ║
║  a refund", it can only guess at what YOU would do.                     ║
║                                                                          ║
║  The SOLUTION — RAG:                                                     ║
║  1. INDEX: Take your past resolved tickets, product docs, policies.     ║
║             Convert them to numerical vectors (embeddings).              ║
║             Store the vectors in Qdrant (a vector database).            ║
║                                                                          ║
║  2. QUERY: When a new ticket comes in ("Package arrived damaged"):       ║
║             Convert the query to a vector.                               ║
║             Search Qdrant for the MOST SIMILAR past tickets.            ║
║             Retrieve the top 5 most similar historical resolutions.     ║
║             Inject those into the agent's prompt as context.            ║
║             Now the agent knows: "Last time a package was damaged,      ║
║             we issued a 15% refund AND sent a replacement."             ║
║                                                                          ║
║  WHY VECTORS?                                                            ║
║  "Package damaged" and "item arrived broken" are DIFFERENT WORDS but    ║
║  SAME MEANING. Keywords search wouldn't match them. But as vectors,     ║
║  they're CLOSE in vector space → cosine similarity finds them.         ║
║                                                                          ║
║  WHAT IS QDRANT?                                                         ║
║  Qdrant is a vector database — like PostgreSQL but stores and queries   ║
║  high-dimensional floating point vectors instead of rows and columns.   ║
║  Runs in Docker (see docker-compose.yml, image: qdrant/qdrant:latest)  ║
║  Accessible at: http://localhost:6333                                    ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os     # to read environment variables (QDRANT_URL, OPENAI_API_KEY)
import uuid   # generates unique IDs for documents (e.g. "b4f2a1d0-8c3e-...")
from typing import Optional  # for type hints (Optional[str] = str | None)

# ── LangChain components ───────────────────────────────────────────────────────
# OpenAIEmbeddings: converts text to 1536-dimensional floating-point vectors.
# "text-embedding-3-small" is a specialized model just for embeddings (not generation).
# It takes text → outputs [0.123, -0.456, 0.789, ...] (1536 numbers).
# Two pieces of text with similar meaning → similar vectors → high cosine similarity.
from langchain_openai import OpenAIEmbeddings

# Qdrant: LangChain's wrapper for the Qdrant vector database.
# This adapter lets us use Qdrant with LangChain's vectorstore interface.
# The interface: add_documents(docs) and similarity_search(query, k=5)
from langchain_community.vectorstores import Qdrant

# RecursiveCharacterTextSplitter: splits long documents into smaller chunks.
# WHY SPLIT? LLMs have context limits. A 10,000-word document can't be embedded
# as one piece. We split into 1000-character chunks with 100-char overlap.
# The overlap ensures that a sentence split across chunk boundary
# isn't lost — both chunks share the 100-char border.
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Document: LangChain's standard document format.
# page_content = the text to embed
# metadata = dict of extra info (ticket_id, source type, etc.)
# Metadata is stored with the vector so you can trace back which ticket matched.
from langchain.schema import Document

# ── Qdrant client ──────────────────────────────────────────────────────────────
# AsyncQdrantClient: async version (use inside async functions like init_qdrant)
# QdrantClient: sync version (fine for regular functions like get_vector_store)
from qdrant_client import AsyncQdrantClient, QdrantClient

# models for configuring vector collections in Qdrant
# Distance.COSINE: use cosine similarity to measure how similar two vectors are.
#   Cosine similarity = dot product of vectors ÷ product of their magnitudes.
#   Value: 1.0 = identical meaning, 0.0 = unrelated, -1.0 = opposite meaning.
# VectorParams: tells Qdrant the size and distance metric for this collection.
from qdrant_client.models import Distance, VectorParams


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: Constants
# ═══════════════════════════════════════════════════════════════════════════════

# The name of the Qdrant "collection" (like a database table, but for vectors).
# All ticket, product, and policy vectors go in one collection.
# We use metadata filters (source="support_ticket") to distinguish them.
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "nexusos_embeddings")

# Where Qdrant is running. In Docker Compose: "nexusos-qdrant" container at port 6333.
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# How many dimensions the embedding vectors have.
# "text-embedding-3-small" outputs exactly 1536 floats per text.
# This MUST match when creating the Qdrant collection (VectorParams size below).
EMBEDDING_DIM = 1536  # OpenAI text-embedding-3-small dimension


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: Embedding Model Setup
# ═══════════════════════════════════════════════════════════════════════════════

def get_embeddings() -> OpenAIEmbeddings:
    """
    Returns a configured OpenAI embeddings model instance.

    WHAT IS AN EMBEDDING MODEL?
    Different from a chat model (ChatOpenAI). This model doesn't generate
    conversational text — it converts TEXT into NUMBERS (vectors).

    "text-embedding-3-small":
    - OpenAI's latest small embedding model
    - Outputs 1536-dimensional vectors
    - Best for semantic similarity search (what we need for RAG)
    - Much cheaper than chat models: $0.02 per 1M tokens (essentially free)
    - "Small" means it's fast and cheap, not that it's bad at embeddings

    WHEN IT'S CALLED:
    - When indexing new support tickets (to embed the ticket text)
    - When querying (to embed the search query before Qdrant similarity search)
    Both the stored vectors AND the query vector must use the SAME model.
    Otherwise, their "languages" don't match and similarity scores are meaningless.
    """
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),  # reads from .env
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: Qdrant Initialization
# ═══════════════════════════════════════════════════════════════════════════════

async def init_qdrant():
    """
    Create the Qdrant collection on first startup (if it doesn't exist).

    CALLED BY: main.py startup lifespan hook.
    This runs ONCE when the FastAPI server starts.

    WHY ASYNC?
    This function uses `await` to make non-blocking network calls to Qdrant.
    In async Python, `await` means "wait for this to complete, but don't block
    other concurrent work while waiting."
    The `async` keyword before `def` marks this as an "awaitable" coroutine.

    IDEMPOTENT: Safe to call multiple times.
    If the collection already exists, we print a message and continue.
    We don't delete and recreate it (that would lose all stored vectors!).

    WHAT IS A COLLECTION IN QDRANT?
    Like a "table" in PostgreSQL. One collection = one group of related vectors.
    All stored with the same dimension (1536) and distance metric (COSINE).
    """
    # Create an async Qdrant client.
    # AsyncQdrantClient communicates with the Qdrant HTTP API at QDRANT_URL.
    client = AsyncQdrantClient(url=QDRANT_URL)

    try:
        # Get list of all existing collections from Qdrant.
        # This is a network call (the client talks to the Docker container).
        collections = await client.get_collections()

        # Extract just the collection names from the response objects.
        # collections.collections is a list of CollectionDescription objects.
        # Each has a .name attribute. List comprehension extracts just the names.
        existing = [c.name for c in collections.collections]

        if COLLECTION_NAME not in existing:
            # Collection doesn't exist yet — create it.
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                # VectorParams tells Qdrant:
                #   size=1536 → each vector is 1536 floats
                #   distance=COSINE → compare vectors using cosine similarity
                # This MUST match the embedding model's output dimension.
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )
            print(f"[qdrant] ✅ Created collection: {COLLECTION_NAME}")
        else:
            # Already exists — don't touch it, just confirm it's there.
            print(f"[qdrant] ✅ Collection already exists: {COLLECTION_NAME}")

    except Exception as e:
        # If Qdrant is down (e.g., Docker container hasn't started yet),
        # we don't crash — we just warn and continue.
        # The service can still handle requests; RAG will be unavailable
        # but the rest of the system works fine.
        print(f"[qdrant] ⚠️ Warning: init failed ({e}) — Qdrant may not be running")

    finally:
        # ALWAYS close the client, even if an exception was raised.
        # `finally` block runs regardless of success or failure.
        # Closing releases the network connection back to the pool.
        await client.close()


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: Vector Store Instance
# ═══════════════════════════════════════════════════════════════════════════════

def get_vector_store() -> Qdrant:
    """
    Returns a LangChain Qdrant vector store instance.

    HOW THE VECTOR STORE WORKS:
    This is LangChain's abstraction layer over Qdrant. Instead of:
      1. Call OpenAI embeddings API to get vector for text
      2. Call Qdrant API to store {vector, metadata}
    You just call: store.add_documents([Document(text, metadata)])
    LangChain handles steps 1 and 2 automatically.

    SYNCHRONOUS (not async): The sync QdrantClient is used here because
    LangChain's Qdrant wrapper doesn't natively support async add_documents.
    For startup init, we use AsyncQdrantClient (above).
    For read/write operations at request time, sync client is fine
    because _run() is called in asyncio.to_thread() from the async routers.

    Returns:
        A Qdrant instance with the embeddings model pre-attached.
    """
    # Synchronous Qdrant client for use in non-async functions
    client = QdrantClient(url=QDRANT_URL)

    # Return LangChain's Qdrant vectorstore wrapper.
    # Combines the Qdrant storage backend with the embeddings model.
    return Qdrant(
        client=client,           # where to store/retrieve vectors
        collection_name=COLLECTION_NAME,  # which collection
        embeddings=get_embeddings(),      # which model to use for embedding
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PART 5: Indexing Functions
# ═══════════════════════════════════════════════════════════════════════════════

def index_support_ticket(
    ticket_id: str,
    subject: str,
    body: str,
    resolution: Optional[str] = None,
):
    """
    Embed and store a support ticket in Qdrant for future retrieval.

    WHEN TO CALL THIS:
    1. When a ticket is CREATED (so future tickets can find similar ones)
    2. When a ticket is RESOLVED (to include the resolution in the context)
       — The resolution is THE MOST IMPORTANT PART for RAG. The agent needs
         to know not just WHAT the problem was, but HOW IT WAS RESOLVED.

    THE CHUNKING STEP:
    A support ticket might be 2000 characters. We can't embed it as one piece
    because we'd lose nuance when comparing partial concepts.
    We split into 1000-char chunks with 100-char overlap.
    Each chunk becomes a separate vector in Qdrant, all tagged with the same ticket_id.
    When querying, we might retrieve chunk 2 of ticket #892 (the resolution part)
    which is more relevant than chunk 1 (the problem description).

    Args:
        ticket_id: Unique ID for this ticket (e.g., from PostgreSQL UUID)
        subject: The email/ticket subject line
        body: The full ticket body text
        resolution: (Optional) How the ticket was resolved. Include whenever possible.
    """
    # Combine all text into one string first.
    # String concatenation: "Subject: " + subject + "\n\n" + "Ticket: " + body
    # f-strings are just cleaner syntax for the same thing.
    text = f"Subject: {subject}\n\nTicket: {body}"

    # If we know the resolution, append it. This makes RAG much more useful:
    # when the agent searches for similar tickets, it sees the solution too.
    if resolution:
        text += f"\n\nResolution: {resolution}"

    # TextSplitter: breaks the full text into smaller chunks for embedding.
    # chunk_size=1000: each chunk is at most 1000 characters
    # chunk_overlap=100: adjacent chunks share 100 characters at the boundary
    #   This prevents losing information at chunk boundaries. If a sentence is:
    #   "...issued a replacement[boundary]and refunded shipping costs..."
    #   Without overlap: "refunded shipping costs" is orphaned from its context.
    #   With overlap: both chunks around the boundary include the overlap text.
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(text)  # returns a list of strings

    # Wrap each chunk in a Document object with metadata.
    # metadata is stored alongside the vector in Qdrant.
    # When similarity_search returns results, the metadata comes with them —
    # we can trace back which ticket_id matched and show it to the agent.
    docs = [
        Document(
            page_content=chunk,   # the text to embed
            metadata={
                "source": "support_ticket",  # what type of document this is
                "ticket_id": ticket_id,       # which ticket this chunk came from
                "chunk_index": i,             # which chunk within the ticket (0, 1, 2...)
            },
        )
        # List comprehension: creates one Document per chunk, with index i.
        # `enumerate(chunks)` gives (index, chunk) pairs: (0, "Subject: ..."), (1, "...")
        for i, chunk in enumerate(chunks)
    ]

    # Add all chunks to Qdrant in one batch call.
    # Under the hood, LangChain:
    # 1. Calls OpenAI embedding API on all chunks (batched for efficiency)
    # 2. Calls Qdrant's upsert API to store {vector, metadata} for each chunk
    store = get_vector_store()
    store.add_documents(docs)
    print(f"[rag] Indexed ticket {ticket_id} ({len(docs)} chunks)")


def index_product_doc(product_id: str, title: str, description: str, policy: Optional[str] = None):
    """
    Embed and store a product document in Qdrant.

    WHY INDEX PRODUCT DOCS?
    When a customer asks "Does the Charizard PSA 9 card come with a certificate?",
    the SupportAgent needs to know your product details.
    With RAG, it finds the Charizard product doc and answers accurately.

    WITHOUT RAG: Agent guesses (and might be wrong about condition, included items, etc.)
    WITH RAG:    Agent retrieves "Product: Charizard PSA 9. Includes: PSA slab, COA booklet."

    Args:
        product_id: Shopify product ID
        title: Product name (e.g., "Charizard Holo 1st Edition PSA 9")
        description: Full product description
        policy: (Optional) product-specific return/exchange policy
    """
    text = f"Product: {title}\n\nDescription: {description}"
    if policy:
        text += f"\n\nReturn Policy: {policy}"

    # Single Document (no chunking needed — product docs are usually short)
    doc = Document(
        page_content=text,
        metadata={"source": "product_doc", "product_id": product_id},
    )

    store = get_vector_store()
    store.add_documents([doc])  # pass as a list (add_documents takes a list)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 6: Retrieval Functions (used by agents at query time)
# ═══════════════════════════════════════════════════════════════════════════════

def retrieve_context(query: str, merchant_id: str, k: int = 5) -> str:
    """
    Find the most relevant historical context for a query.

    This is the "R" in RAG — the Retrieval step.
    Agents call this before making decisions to get relevant past context.

    HOW VECTOR SIMILARITY SEARCH WORKS:
    1. Take the query string ("package arrived damaged")
    2. Call OpenAI embedding API → get a vector [0.12, -0.34, ...]  (1536 numbers)
    3. Compare that vector to EVERY vector in Qdrant using cosine similarity
    4. Return the k=5 documents with the HIGHEST cosine similarity scores
    These top-k documents are the most semantically similar content we have stored.

    WHY k=5?
    5 gives enough context without overwhelming the agent's prompt.
    Each retrieved document adds ~1000 chars to the prompt.
    5 documents = ~5000 extra chars = well within Claude/GPT-4o's 128K token context.

    Args:
        query: What we're searching for (the new ticket subject or question)
        merchant_id: Used for future per-merchant filtering (multi-tenant RAG)
        k: How many documents to retrieve (default 5)

    Returns:
        A single string combining the k most relevant document texts,
        separated by "---" dividers for readability. This gets injected into the agent's prompt.
    """
    store = get_vector_store()

    try:
        # similarity_search(query, k=5):
        # 1. Embeds the query string using OpenAI
        # 2. Does approximate nearest-neighbor search in Qdrant
        # 3. Returns k Document objects ordered by similarity (highest first)
        results = store.similarity_search(query, k=k)

        if not results:
            # No similar documents found.
            # This happens when the RAG index is empty (no tickets indexed yet).
            return "No relevant historical context found."

        # Build a formatted context string from all retrieved documents.
        context_parts = []
        for i, doc in enumerate(results, 1):  # enumerate starting at 1 (not 0 — more human)
            # doc.metadata["source"] tells us if this is a "support_ticket" or "product_doc"
            source = doc.metadata.get("source", "unknown")
            # Format: "[Context 1 — support_ticket]\n{content}"
            context_parts.append(f"[Context {i} — {source}]\n{doc.page_content}")

        # "\n\n---\n\n".join(list) puts the separator string between all items.
        # Result: "[Context 1 — support_ticket]\n...\n\n---\n\n[Context 2 — ...]\n..."
        return "\n\n---\n\n".join(context_parts)

    except Exception as e:
        # If Qdrant is temporarily unavailable, return a graceful fallback.
        # The agent can still function — it just won't have historical context.
        print(f"[rag] Retrieval error: {e}")
        return "Context retrieval temporarily unavailable."


def build_rag_prompt(query: str, context: str, system_role: str) -> str:
    """
    Build a complete RAG-augmented prompt for an LLM call.

    WHAT IS PROMPT ENGINEERING?
    The way you structure a prompt dramatically affects LLM output quality.
    RAG prompts have a specific structure:
      1. System role (who is the AI?)
      2. Retrieved context (what does the AI know about this topic?)
      3. The actual question (what do we want answered?)

    WHY THIS ORDER?
    The LLM processes the prompt left-to-right. By giving it the role
    first, then context, then the question — it builds up the right
    "mindset" before reasoning about the specific question.

    Args:
        query: The agent's current question or task description
        context: Output from retrieve_context() — the historical data
        system_role: A description of who the AI is in this context

    Returns:
        A complete prompt string ready to pass to llm.invoke(prompt)
    """
    # Triple-quoted f-string: creates a multi-line string with embedded variables.
    # The === delimiters around RETRIEVED CONTEXT make it visually clear to the
    # LLM where the context starts and ends (improves attention to the right section).
    return f"""You are {system_role}.

Use the following retrieved context to inform your answer. If the context is not relevant, rely on your training knowledge.

=== RETRIEVED CONTEXT ===
{context}
=========================

User Query: {query}

Provide a clear, accurate, and helpful response based on the context above."""
