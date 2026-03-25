-- ============================================================
-- NexusOS Migration 003: Immutable Audit & AI Decision Ledger
-- Append-only by convention + trigger enforcement
-- ============================================================

-- AI Decisions Log (every agent action, immutable)
CREATE TABLE IF NOT EXISTS ai_decisions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    agent_name      TEXT NOT NULL,       -- SupportAgent | LogisticsAgent | FinanceAgent
    task_type       TEXT NOT NULL,       -- refund_eval | reorder_calc | ticket_reply | negotiate
    prompt_hash     TEXT,                -- SHA256 of the prompt (for dedup/auditing)
    model_used      TEXT NOT NULL,       -- ollama:llama3:8b | claude-3-5-sonnet | gpt-4o | o1-preview
    model_cost_usd  NUMERIC(10,6),
    input_tokens    INT,
    output_tokens   INT,
    decision        JSONB NOT NULL,      -- the structured decision made
    outcome         TEXT,                -- success | failure | pending_approval | escalated
    duration_ms     INT,
    trace_id        TEXT,                -- OpenTelemetry trace ID
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audit Log (every significant action, immutable)
CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID REFERENCES merchants(id) ON DELETE RESTRICT,
    actor_type      TEXT NOT NULL,       -- 'ai_agent' | 'human' | 'system' | 'external_agent'
    actor_id        TEXT,
    action          TEXT NOT NULL,
    resource_type   TEXT,
    resource_id     TEXT,
    before_state    JSONB,
    after_state     JSONB,
    ip_address      INET,
    user_agent      TEXT,
    trace_id        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Prevent UPDATE or DELETE on audit tables (write-once ledger)
CREATE OR REPLACE FUNCTION prevent_audit_mutation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Audit tables are append-only. UPDATE/DELETE not permitted.';
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS no_update_ai_decisions ON ai_decisions;
CREATE TRIGGER no_update_ai_decisions
    BEFORE UPDATE OR DELETE ON ai_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();

DROP TRIGGER IF EXISTS no_update_audit_log ON audit_log;
CREATE TRIGGER no_update_audit_log
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ai_decisions_merchant ON ai_decisions(merchant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_decisions_agent ON ai_decisions(agent_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_merchant ON audit_log(merchant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);
