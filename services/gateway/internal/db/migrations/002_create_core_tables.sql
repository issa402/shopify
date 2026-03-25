-- ============================================================
-- NexusOS Migration 002: Core Tables
-- ============================================================

-- Merchants (one row per Shopify store installed)
CREATE TABLE IF NOT EXISTS merchants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shop_domain     TEXT NOT NULL UNIQUE,
    access_token    TEXT NOT NULL,
    scope           TEXT,
    plan            TEXT NOT NULL DEFAULT 'starter', -- starter | growth | enterprise
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    installed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Orders (denormalized from Shopify for fast queries)
CREATE TABLE IF NOT EXISTS orders (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    shopify_id      BIGINT NOT NULL,
    order_number    TEXT,
    email           TEXT,
    total_price     NUMERIC(12,2),
    currency        CHAR(3),
    financial_status TEXT,
    fulfillment_status TEXT,
    tags            TEXT[],
    line_items      JSONB,
    shopify_created_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(merchant_id, shopify_id)
);

-- Customers (enriched profile)
CREATE TABLE IF NOT EXISTS customers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    shopify_id      BIGINT NOT NULL,
    email           TEXT,
    first_name      TEXT,
    last_name       TEXT,
    phone           TEXT,
    tags            TEXT[],
    orders_count    INT DEFAULT 0,
    total_spent     NUMERIC(12,2) DEFAULT 0,
    predicted_ltv   NUMERIC(12,2),     -- AI-computed
    ltv_segment     TEXT,              -- high | medium | low
    shopify_created_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(merchant_id, shopify_id)
);

-- Products
CREATE TABLE IF NOT EXISTS products (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    shopify_id      BIGINT NOT NULL,
    title           TEXT,
    handle          TEXT,
    vendor          TEXT,
    product_type    TEXT,
    tags            TEXT[],
    status          TEXT,
    variants        JSONB,
    shopify_created_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(merchant_id, shopify_id)
);

-- Inventory Levels
CREATE TABLE IF NOT EXISTS inventory_levels (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    inventory_item_id BIGINT NOT NULL,
    location_id     BIGINT,
    available       INT NOT NULL DEFAULT 0,
    reorder_point   INT,           -- AI-computed reorder threshold
    reorder_qty     INT,           -- AI-suggested order quantity
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(merchant_id, inventory_item_id, location_id)
);

-- Support Tickets
CREATE TABLE IF NOT EXISTS support_tickets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    customer_id     UUID REFERENCES customers(id),
    subject         TEXT,
    body            TEXT,
    status          TEXT NOT NULL DEFAULT 'open', -- open | in_progress | resolved | escalated
    priority        TEXT NOT NULL DEFAULT 'normal', -- urgent | normal | low
    resolution      TEXT,
    resolved_by     TEXT, -- 'ai' | 'human' | 'hybrid'
    embedding       vector(1536),  -- semantic search vector
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Workflow Rules (IFTTT engine)
CREATE TABLE IF NOT EXISTS workflow_rules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    description     TEXT,
    trigger_event   TEXT NOT NULL,  -- e.g. 'order.created', 'inventory.low'
    conditions      JSONB,          -- array of condition objects
    actions         JSONB,          -- array of action objects
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    run_count       BIGINT NOT NULL DEFAULT 0,
    last_run_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Approval Queue (Human-in-the-Loop)
CREATE TABLE IF NOT EXISTS approval_queue (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    agent_name      TEXT NOT NULL,
    action_type     TEXT NOT NULL,  -- e.g. 'refund', 'po_create', 'data_delete'
    action_payload  JSONB NOT NULL,
    estimated_cost  NUMERIC(12,2),
    status          TEXT NOT NULL DEFAULT 'pending', -- pending | approved | rejected
    decided_by      TEXT,          -- user ID who approved/rejected
    decided_at      TIMESTAMPTZ,
    reason          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_orders_merchant_id ON orders(merchant_id);
CREATE INDEX IF NOT EXISTS idx_orders_shopify_id ON orders(shopify_id);
CREATE INDEX IF NOT EXISTS idx_customers_merchant_id ON customers(merchant_id);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_products_merchant_id ON products(merchant_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_merchant_id ON support_tickets(merchant_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_approval_queue_merchant_status ON approval_queue(merchant_id, status);

-- Vector index for semantic search on support tickets
CREATE INDEX IF NOT EXISTS idx_support_tickets_embedding
ON support_tickets USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
