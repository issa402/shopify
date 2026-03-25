-- ============================================================
-- NexusOS Migration 004: Row-Level Security Policies
-- Every merchant sees ONLY their own data
-- ============================================================

-- Enable RLS on all tenant tables
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_levels ENABLE ROW LEVEL SECURITY;
ALTER TABLE support_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Application sets current_setting('app.current_merchant_id') on each connection
-- RLS policies enforce data isolation at the database level

CREATE POLICY merchant_isolation_orders ON orders
    USING (merchant_id = current_setting('app.current_merchant_id')::UUID);

CREATE POLICY merchant_isolation_customers ON customers
    USING (merchant_id = current_setting('app.current_merchant_id')::UUID);

CREATE POLICY merchant_isolation_products ON products
    USING (merchant_id = current_setting('app.current_merchant_id')::UUID);

CREATE POLICY merchant_isolation_inventory ON inventory_levels
    USING (merchant_id = current_setting('app.current_merchant_id')::UUID);

CREATE POLICY merchant_isolation_tickets ON support_tickets
    USING (merchant_id = current_setting('app.current_merchant_id')::UUID);

CREATE POLICY merchant_isolation_workflows ON workflow_rules
    USING (merchant_id = current_setting('app.current_merchant_id')::UUID);

CREATE POLICY merchant_isolation_approvals ON approval_queue
    USING (merchant_id = current_setting('app.current_merchant_id')::UUID);

CREATE POLICY merchant_isolation_ai_decisions ON ai_decisions
    USING (merchant_id = current_setting('app.current_merchant_id')::UUID);

CREATE POLICY merchant_isolation_audit ON audit_log
    USING (merchant_id = current_setting('app.current_merchant_id')::UUID);

-- Service role bypasses RLS (for admin/migration operations only)
CREATE ROLE nexusos_service NOLOGIN;
ALTER TABLE orders FORCE ROW LEVEL SECURITY;
ALTER TABLE customers FORCE ROW LEVEL SECURITY;
ALTER TABLE products FORCE ROW LEVEL SECURITY;
