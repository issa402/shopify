// Package dashboard exposes merchant dashboard data from real NexusOS tables.
package dashboard

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Handler owns dashboard and operator-facing API endpoints.
type Handler struct {
	db *pgxpool.Pool
}

// NewHandler creates a dashboard handler backed by Postgres.
func NewHandler(db *pgxpool.Pool) *Handler {
	return &Handler{db: db}
}

type merchantContext struct {
	ID         string
	ShopDomain string
	Installed  bool
}

type recentOrder struct {
	OrderNumber       string  `json:"order_number"`
	CustomerEmail     string  `json:"customer_email"`
	TotalPrice        float64 `json:"total_price"`
	FinancialStatus   string  `json:"financial_status"`
	FulfillmentStatus string  `json:"fulfillment_status"`
}

type revenuePoint struct {
	Day       string  `json:"day"`
	Revenue   float64 `json:"revenue"`
	AIActions int     `json:"ai_actions"`
}

type decisionRow struct {
	ID        string  `json:"id"`
	Agent     string  `json:"agent"`
	TaskType  string  `json:"task_type"`
	Model     string  `json:"model"`
	CostUSD   float64 `json:"cost_usd"`
	Outcome   string  `json:"outcome"`
	CreatedAt string  `json:"created_at"`
	Decision  any     `json:"decision"`
}

type approvalRow struct {
	ID            string         `json:"id"`
	Agent         string         `json:"agent"`
	ActionType    string         `json:"action_type"`
	ActionPayload map[string]any `json:"action_payload"`
	EstimatedCost float64        `json:"estimated_cost"`
	Status        string         `json:"status"`
	CreatedAt     string         `json:"created_at"`
}

type customerRow struct {
	ID             string   `json:"id"`
	ShopifyID      int64    `json:"shopify_id"`
	Email          string   `json:"email"`
	FirstName      string   `json:"first_name"`
	LastName       string   `json:"last_name"`
	Phone          string   `json:"phone"`
	Tags           []string `json:"tags"`
	OrdersCount    int      `json:"orders_count"`
	TotalSpent     float64  `json:"total_spent"`
	PredictedLTV   float64  `json:"predicted_ltv"`
	LTVSegment     string   `json:"ltv_segment"`
	ShopifyCreated string   `json:"shopify_created_at"`
}

type workflowRow struct {
	ID          string           `json:"id"`
	Name        string           `json:"name"`
	Description string           `json:"description"`
	Trigger     string           `json:"trigger"`
	Conditions  []map[string]any `json:"conditions"`
	Actions     []map[string]any `json:"actions"`
	Active      bool             `json:"active"`
	RunCount    int64            `json:"run_count"`
}

type createWorkflowRequest struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Trigger     string `json:"trigger"`
	Condition   string `json:"condition"`
	Action      string `json:"action"`
}

// Overview returns the dashboard data needed by the React app.
func (h *Handler) Overview(c *gin.Context) {
	ctx := c.Request.Context()
	merchant, err := h.resolveMerchant(ctx, c.GetString("merchant_id"))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if !merchant.Installed {
		c.JSON(http.StatusOK, gin.H{
			"setup_required": true,
			"merchant":       nil,
			"metrics": gin.H{
				"revenue_today":       0,
				"ai_actions_today":    0,
				"pending_approvals":   0,
				"llm_cost_today_usd":  0,
				"orders_today":        0,
				"autonomous_rate_pct": 0,
			},
			"revenue_series": []revenuePoint{},
			"recent_orders":  []recentOrder{},
			"agent_stats":    []gin.H{},
		})
		return
	}

	tx, err := h.beginMerchantTx(ctx, merchant.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer tx.Rollback(ctx)

	metrics, err := h.metrics(ctx, tx, merchant.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	series, err := h.revenueSeries(ctx, tx, merchant.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	orders, err := h.recentOrders(ctx, tx, merchant.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	stats, err := h.agentStats(ctx, tx, merchant.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"setup_required": false,
		"merchant": gin.H{
			"id":          merchant.ID,
			"shop_domain": merchant.ShopDomain,
		},
		"metrics":        metrics,
		"revenue_series": series,
		"recent_orders":  orders,
		"agent_stats":    stats,
	})
}

// Decisions returns recent AI decision ledger rows.
func (h *Handler) Decisions(c *gin.Context) {
	merchant, tx, ok := h.merchantTx(c)
	if !ok {
		return
	}
	defer tx.Rollback(c.Request.Context())

	rows, err := tx.Query(c.Request.Context(), `
		SELECT id::text, agent_name, task_type, model_used,
		       COALESCE(model_cost_usd, 0)::float8, COALESCE(outcome, ''),
		       created_at::text, decision
		FROM ai_decisions
		WHERE merchant_id = $1
		ORDER BY created_at DESC
		LIMIT 100
	`, merchant.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	decisions := []decisionRow{}
	for rows.Next() {
		var d decisionRow
		var decisionJSON []byte
		if err := rows.Scan(&d.ID, &d.Agent, &d.TaskType, &d.Model, &d.CostUSD, &d.Outcome, &d.CreatedAt, &decisionJSON); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		if err := decodeJSON(decisionJSON, &d.Decision); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		decisions = append(decisions, d)
	}
	if err := rows.Err(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"merchant_id": merchant.ID, "decisions": decisions})
}

// Orders returns recent Shopify orders for the merchant.
func (h *Handler) Orders(c *gin.Context) {
	merchant, tx, ok := h.merchantTx(c)
	if !ok {
		return
	}
	defer tx.Rollback(c.Request.Context())

	orders, err := h.recentOrders(c.Request.Context(), tx, merchant.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"merchant_id": merchant.ID, "orders": orders})
}

// Customers returns recent Shopify customers for the merchant.
func (h *Handler) Customers(c *gin.Context) {
	merchant, tx, ok := h.merchantTx(c)
	if !ok {
		return
	}
	defer tx.Rollback(c.Request.Context())

	rows, err := tx.Query(c.Request.Context(), `
		SELECT id::text, shopify_id, COALESCE(email, ''), COALESCE(first_name, ''),
		       COALESCE(last_name, ''), COALESCE(phone, ''), COALESCE(tags, ARRAY[]::TEXT[]),
		       COALESCE(orders_count, 0), COALESCE(total_spent, 0)::float8,
		       COALESCE(predicted_ltv, 0)::float8, COALESCE(ltv_segment, ''),
		       COALESCE(shopify_created_at, created_at)::text
		FROM customers
		WHERE merchant_id = $1
		ORDER BY COALESCE(shopify_created_at, created_at) DESC
		LIMIT 100
	`, merchant.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	customers := []customerRow{}
	for rows.Next() {
		var customer customerRow
		if err := rows.Scan(
			&customer.ID,
			&customer.ShopifyID,
			&customer.Email,
			&customer.FirstName,
			&customer.LastName,
			&customer.Phone,
			&customer.Tags,
			&customer.OrdersCount,
			&customer.TotalSpent,
			&customer.PredictedLTV,
			&customer.LTVSegment,
			&customer.ShopifyCreated,
		); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		customers = append(customers, customer)
	}
	if err := rows.Err(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"merchant_id": merchant.ID, "customers": customers})
}

// PendingApprovals returns approval queue items that still need review.
func (h *Handler) PendingApprovals(c *gin.Context) {
	merchant, tx, ok := h.merchantTx(c)
	if !ok {
		return
	}
	defer tx.Rollback(c.Request.Context())

	rows, err := tx.Query(c.Request.Context(), `
		SELECT id::text, agent_name, action_type, action_payload,
		       COALESCE(estimated_cost, 0)::float8, status, created_at::text
		FROM approval_queue
		WHERE merchant_id = $1 AND status = 'pending'
		ORDER BY created_at ASC
	`, merchant.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	approvals := []approvalRow{}
	for rows.Next() {
		var a approvalRow
		var payloadJSON []byte
		if err := rows.Scan(&a.ID, &a.Agent, &a.ActionType, &payloadJSON, &a.EstimatedCost, &a.Status, &a.CreatedAt); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		if err := decodeJSON(payloadJSON, &a.ActionPayload); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		approvals = append(approvals, a)
	}
	if err := rows.Err(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"merchant_id": merchant.ID, "pending": approvals})
}

// DecideApproval approves or rejects a pending approval queue item.
func (h *Handler) DecideApproval(status string) gin.HandlerFunc {
	return func(c *gin.Context) {
		merchant, tx, ok := h.merchantTx(c)
		if !ok {
			return
		}
		defer tx.Rollback(c.Request.Context())

		tag, err := tx.Exec(c.Request.Context(), `
			UPDATE approval_queue
			SET status = $1, decided_at = NOW(), decided_by = $2
			WHERE id = $3 AND merchant_id = $4 AND status = 'pending'
		`, status, c.GetString("role"), c.Param("id"), merchant.ID)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		if tag.RowsAffected() == 0 {
			c.JSON(http.StatusNotFound, gin.H{"error": "approval not found or already decided"})
			return
		}
		if err := tx.Commit(c.Request.Context()); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"status": status, "id": c.Param("id")})
	}
}

// Workflows lists stored workflow rules.
func (h *Handler) Workflows(c *gin.Context) {
	merchant, tx, ok := h.merchantTx(c)
	if !ok {
		return
	}
	defer tx.Rollback(c.Request.Context())

	rows, err := tx.Query(c.Request.Context(), `
		SELECT id::text, name, COALESCE(description, ''), trigger_event,
		       conditions, actions, is_active, run_count
		FROM workflow_rules
		WHERE merchant_id = $1
		ORDER BY created_at DESC
	`, merchant.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	workflows := []workflowRow{}
	for rows.Next() {
		var w workflowRow
		var conditionsJSON []byte
		var actionsJSON []byte
		if err := rows.Scan(&w.ID, &w.Name, &w.Description, &w.Trigger, &conditionsJSON, &actionsJSON, &w.Active, &w.RunCount); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		if err := decodeJSON(conditionsJSON, &w.Conditions); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		if err := decodeJSON(actionsJSON, &w.Actions); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		workflows = append(workflows, w)
	}
	if err := rows.Err(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"merchant_id": merchant.ID, "workflows": workflows})
}

// CreateWorkflow persists a merchant workflow rule.
func (h *Handler) CreateWorkflow(c *gin.Context) {
	merchant, tx, ok := h.merchantTx(c)
	if !ok {
		return
	}
	defer tx.Rollback(c.Request.Context())

	var input createWorkflowRequest
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if input.Name == "" || input.Trigger == "" || input.Action == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "name, trigger, and action are required"})
		return
	}

	condition := input.Condition
	if condition == "" {
		condition = "always"
	}
	conditions, _ := json.Marshal([]gin.H{{"expression": condition}})
	actions, _ := json.Marshal([]gin.H{{"command": input.Action}})

	var id string
	if err := tx.QueryRow(c.Request.Context(), `
		INSERT INTO workflow_rules (merchant_id, name, description, trigger_event, conditions, actions)
		VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb)
		RETURNING id::text
	`, merchant.ID, input.Name, input.Description, input.Trigger, string(conditions), string(actions)).Scan(&id); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if err := tx.Commit(c.Request.Context()); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, gin.H{"id": id, "status": "created"})
}

// ToggleWorkflow flips a workflow rule between active and paused.
func (h *Handler) ToggleWorkflow(c *gin.Context) {
	merchant, tx, ok := h.merchantTx(c)
	if !ok {
		return
	}
	defer tx.Rollback(c.Request.Context())

	var active bool
	err := tx.QueryRow(c.Request.Context(), `
		UPDATE workflow_rules
		SET is_active = NOT is_active
		WHERE id = $1 AND merchant_id = $2
		RETURNING is_active
	`, c.Param("id"), merchant.ID).Scan(&active)
	if err == pgx.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "workflow not found"})
		return
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if err := tx.Commit(c.Request.Context()); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"id": c.Param("id"), "active": active})
}

func (h *Handler) merchantTx(c *gin.Context) (merchantContext, pgx.Tx, bool) {
	ctx := c.Request.Context()
	merchant, err := h.resolveMerchant(ctx, c.GetString("merchant_id"))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return merchantContext{}, nil, false
	}
	if !merchant.Installed {
		c.JSON(http.StatusOK, gin.H{"setup_required": true, "merchant": nil})
		return merchantContext{}, nil, false
	}
	tx, err := h.beginMerchantTx(ctx, merchant.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return merchantContext{}, nil, false
	}
	return merchant, tx, true
}

func (h *Handler) resolveMerchant(ctx context.Context, requestedID string) (merchantContext, error) {
	var m merchantContext
	if requestedID != "" {
		err := h.db.QueryRow(ctx, `
			SELECT id::text, shop_domain FROM merchants WHERE id = $1 AND is_active = TRUE
		`, requestedID).Scan(&m.ID, &m.ShopDomain)
		if err == nil {
			m.Installed = true
			return m, nil
		}
		if err != pgx.ErrNoRows {
			return m, err
		}
	}

	err := h.db.QueryRow(ctx, `
		SELECT id::text, shop_domain FROM merchants WHERE is_active = TRUE ORDER BY installed_at ASC LIMIT 1
	`).Scan(&m.ID, &m.ShopDomain)
	if err == pgx.ErrNoRows {
		return merchantContext{Installed: false}, nil
	}
	if err != nil {
		return merchantContext{}, err
	}
	m.Installed = true
	return m, nil
}

func (h *Handler) beginMerchantTx(ctx context.Context, merchantID string) (pgx.Tx, error) {
	tx, err := h.db.Begin(ctx)
	if err != nil {
		return nil, err
	}
	if _, err := tx.Exec(ctx, `SELECT set_config('app.current_merchant_id', $1, TRUE)`, merchantID); err != nil {
		tx.Rollback(ctx)
		return nil, fmt.Errorf("failed to set merchant context: %w", err)
	}
	return tx, nil
}

func decodeJSON(data []byte, target any) error {
	if len(data) == 0 || string(data) == "null" {
		return nil
	}
	return json.Unmarshal(data, target)
}

func (h *Handler) metrics(ctx context.Context, tx pgx.Tx, merchantID string) (gin.H, error) {
	var revenueToday float64
	var ordersToday int
	if err := tx.QueryRow(ctx, `
		SELECT COALESCE(SUM(total_price), 0)::float8, COUNT(*)
		FROM orders
		WHERE merchant_id = $1 AND created_at::date = CURRENT_DATE
	`, merchantID).Scan(&revenueToday, &ordersToday); err != nil {
		return nil, err
	}

	var aiActions int
	var llmCost float64
	if err := tx.QueryRow(ctx, `
		SELECT COUNT(*), COALESCE(SUM(model_cost_usd), 0)::float8
		FROM ai_decisions
		WHERE merchant_id = $1 AND created_at::date = CURRENT_DATE
	`, merchantID).Scan(&aiActions, &llmCost); err != nil {
		return nil, err
	}

	var pending int
	if err := tx.QueryRow(ctx, `
		SELECT COUNT(*) FROM approval_queue WHERE merchant_id = $1 AND status = 'pending'
	`, merchantID).Scan(&pending); err != nil {
		return nil, err
	}

	var completed int
	var escalated int
	if err := tx.QueryRow(ctx, `
		SELECT
			COUNT(*) FILTER (WHERE outcome IN ('success', 'pending_approval'))::int,
			COUNT(*) FILTER (WHERE outcome IN ('failure', 'escalated'))::int
		FROM ai_decisions
		WHERE merchant_id = $1 AND created_at::date = CURRENT_DATE
	`, merchantID).Scan(&completed, &escalated); err != nil {
		return nil, err
	}
	rate := 0
	if completed+escalated > 0 {
		rate = int(float64(completed) / float64(completed+escalated) * 100)
	}

	return gin.H{
		"revenue_today":       revenueToday,
		"orders_today":        ordersToday,
		"ai_actions_today":    aiActions,
		"pending_approvals":   pending,
		"llm_cost_today_usd":  llmCost,
		"autonomous_rate_pct": rate,
	}, nil
}

func (h *Handler) revenueSeries(ctx context.Context, tx pgx.Tx, merchantID string) ([]revenuePoint, error) {
	rows, err := tx.Query(ctx, `
		WITH days AS (
			SELECT generate_series(CURRENT_DATE - INTERVAL '6 days', CURRENT_DATE, INTERVAL '1 day')::date AS day
		)
		SELECT to_char(days.day, 'Dy'),
		       COALESCE(SUM(orders.total_price), 0)::float8,
		       (
		         SELECT COUNT(*) FROM ai_decisions
		         WHERE ai_decisions.merchant_id = $1 AND ai_decisions.created_at::date = days.day
		       )::int
		FROM days
		LEFT JOIN orders ON orders.merchant_id = $1 AND orders.created_at::date = days.day
		GROUP BY days.day
		ORDER BY days.day
	`, merchantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	points := []revenuePoint{}
	for rows.Next() {
		var p revenuePoint
		if err := rows.Scan(&p.Day, &p.Revenue, &p.AIActions); err == nil {
			points = append(points, p)
		}
	}
	return points, rows.Err()
}

func (h *Handler) recentOrders(ctx context.Context, tx pgx.Tx, merchantID string) ([]recentOrder, error) {
	rows, err := tx.Query(ctx, `
		SELECT COALESCE(order_number, shopify_id::text), COALESCE(email, ''),
		       COALESCE(total_price, 0)::float8, COALESCE(financial_status, ''),
		       COALESCE(fulfillment_status, '')
		FROM orders
		WHERE merchant_id = $1
		ORDER BY COALESCE(shopify_created_at, created_at) DESC
		LIMIT 10
	`, merchantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	orders := []recentOrder{}
	for rows.Next() {
		var o recentOrder
		if err := rows.Scan(&o.OrderNumber, &o.CustomerEmail, &o.TotalPrice, &o.FinancialStatus, &o.FulfillmentStatus); err == nil {
			orders = append(orders, o)
		}
	}
	return orders, rows.Err()
}

func (h *Handler) agentStats(ctx context.Context, tx pgx.Tx, merchantID string) ([]gin.H, error) {
	rows, err := tx.Query(ctx, `
		SELECT agent_name, COUNT(*)::int, COALESCE(SUM(model_cost_usd), 0)::float8,
		       MAX(created_at)
		FROM ai_decisions
		WHERE merchant_id = $1 AND created_at >= NOW() - INTERVAL '24 hours'
		GROUP BY agent_name
		ORDER BY agent_name
	`, merchantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	stats := []gin.H{}
	for rows.Next() {
		var name string
		var count int
		var cost float64
		var last time.Time
		if err := rows.Scan(&name, &count, &cost, &last); err == nil {
			status := "Idle"
			if time.Since(last) < 30*time.Minute {
				status = "Active"
			}
			stats = append(stats, gin.H{
				"name":        name,
				"status":      status,
				"resolutions": count,
				"cost_usd":    cost,
			})
		}
	}
	return stats, rows.Err()
}
