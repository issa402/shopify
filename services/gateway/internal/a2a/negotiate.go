// Package a2a implements the Agent-to-Agent Commerce Interface.
// This endpoint allows customer AI agents (e.g., Google-Agent, Perplexity-Agent)
// to negotiate purchases directly with NexusOS via structured JSON protocol.
package a2a

import (
	"encoding/json"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/nexusos/gateway/internal/mcp"
)

// Handler manages A2A commerce endpoint logic.
type Handler struct {
	mcpHub *mcp.Hub
}

// NewHandler creates a new A2A handler.
func NewHandler(hub *mcp.Hub) *Handler {
	return &Handler{mcpHub: hub}
}

// ─── A2A JSON Schema Types ────────────────────────────────────────────────────

// ProductQuery — an AI agent's purchase intent message.
type ProductQuery struct {
	AgentID    string            `json:"agent_id" binding:"required"`
	AgentType  string            `json:"agent_type"` // e.g. "google-shopping-agent"
	SessionID  string            `json:"session_id"`
	Query      string            `json:"query" binding:"required"` // natural language
	Constraints QueryConstraints `json:"constraints"`
	Quantity   int               `json:"quantity"`
}

// QueryConstraints — buyer AI's shopping constraints.
type QueryConstraints struct {
	MaxPriceUSD    float64  `json:"max_price_usd"`
	RequiredTags   []string `json:"required_tags"`
	MaxShippingDays int     `json:"max_shipping_days"`
	PreferredCurrency string `json:"preferred_currency"`
	B2B            bool     `json:"b2b"` // bulk/corporate purchase
}

// Offer — NexusOS response to a ProductQuery.
type Offer struct {
	OfferID       string    `json:"offer_id"`
	SessionID     string    `json:"session_id"`
	Products      []ProductMatch `json:"products"`
	ExpiresAt     time.Time `json:"expires_at"`
	NegotiationURL string   `json:"negotiation_url,omitempty"` // for counter-offers
	Protocol      string    `json:"protocol"` // "nexusos-a2a/1.0"
}

// ProductMatch — a matched product in an Offer.
type ProductMatch struct {
	ProductID   string  `json:"product_id"`
	Title       string  `json:"title"`
	PriceUSD    float64 `json:"price_usd"`
	DiscountPct float64 `json:"discount_pct,omitempty"`
	FinalPrice  float64 `json:"final_price_usd"`
	Inventory   int     `json:"inventory_available"`
	ShippingDays int    `json:"estimated_shipping_days"`
	ASIN        string  `json:"asin,omitempty"` // if applicable
}

// Contract — signed purchase agreement (closes the negotiation).
type Contract struct {
	ContractID  string    `json:"contract_id"`
	SessionID   string    `json:"session_id"`
	OfferID     string    `json:"offer_id"`
	AgentID     string    `json:"agent_id"`
	Products    []ProductMatch `json:"products"`
	TotalUSD    float64   `json:"total_usd"`
	Status      string    `json:"status"` // "accepted" | "pending_payment"
	CreatedAt   time.Time `json:"created_at"`
	PaymentURL  string    `json:"payment_url,omitempty"`
}

// ─── Endpoint: POST /api/v1/agent/negotiate ───────────────────────────────────

// Negotiate handles an incoming A2A purchase negotiation.
// Detects AI agent User-Agent headers and routes to the Negotiation Swarm.
func (h *Handler) Negotiate(c *gin.Context) {
	// Detect AI agent from User-Agent header
	userAgent := c.GetHeader("User-Agent")
	if !isAgentRequest(userAgent) {
		c.JSON(http.StatusForbidden, gin.H{
			"error":   "endpoint_reserved_for_agents",
			"message": "This endpoint is designed for AI agent clients. Human browsers should use the standard storefront.",
		})
		return
	}

	var query ProductQuery
	if err := c.ShouldBindJSON(&query); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "invalid_schema",
			"message": err.Error(),
			"schema":  "https://nexusos.io/schemas/a2a-commerce.json",
		})
		return
	}

	// Assign session ID if not provided
	if query.SessionID == "" {
		query.SessionID = uuid.New().String()
	}

	log.Printf("[a2a] Negotiation request from agent=%s session=%s query=%q", query.AgentID, query.SessionID, query.Query)

	// Forward to Python AI service Negotiation Swarm
	// For now: return a structured demo offer
	offer := h.buildOffer(query)

	// Log to audit trail
	log.Printf("[a2a] Offer %s generated for session %s", offer.OfferID, query.SessionID)

	c.JSON(http.StatusOK, offer)
}

// Capabilities returns the A2A capabilities advertised by this NexusOS instance.
func (h *Handler) Capabilities(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"protocol":  "nexusos-a2a/1.0",
		"version":   "2026.1.0",
		"endpoints": gin.H{
			"negotiate":   "POST /api/v1/agent/negotiate",
			"capabilities": "GET /api/v1/agent/capabilities",
		},
		"supported_operations": []string{
			"product_query",
			"price_negotiation",
			"bulk_order",
			"contract_generation",
			"auto_payment",
		},
		"constraints": gin.H{
			"max_quantity_per_request": 10000,
			"max_discount_pct":         25,
			"supported_currencies":     []string{"USD", "EUR", "GBP", "CAD"},
		},
		"agent_auth": gin.H{
			"required": true,
			"methods":  []string{"bearer_token", "agent_certificate"},
		},
		"schema_url": "https://nexusos.io/schemas/a2a-commerce.json",
	})
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

// isAgentRequest returns true if the User-Agent indicates an AI agent client.
func isAgentRequest(ua string) bool {
	agentSignatures := []string{
		"Google-Agent", "Perplexity-Agent", "OpenAI-Agent",
		"Anthropic-Agent", "NexusOS-Agent", "LangChain",
		"AutoGen", "CrewAI", "AI-Agent",
	}
	ua = strings.ToLower(ua)
	for _, sig := range agentSignatures {
		if strings.Contains(ua, strings.ToLower(sig)) {
			return true
		}
	}
	// Also check for custom header
	return false // In production, also check X-Agent-Type header
}

// buildOffer constructs a demo Offer. In production, this calls the Python AI service.
func (h *Handler) buildOffer(query ProductQuery) Offer {
	offerID := uuid.New().String()

	// Placeholder product matching logic
	// In production: query Postgres via MCP, run margin check via FinanceAgent
	products := []ProductMatch{
		{
			ProductID:    "prod_" + uuid.New().String()[:8],
			Title:        "Example Product matching: " + query.Query,
			PriceUSD:     99.00,
			DiscountPct:  0,
			FinalPrice:   99.00,
			Inventory:    250,
			ShippingDays: 2,
		},
	}

	// Apply B2B bulk discount
	if query.B2B && query.Quantity >= 10 {
		for i := range products {
			products[i].DiscountPct = 10
			products[i].FinalPrice = products[i].PriceUSD * 0.90
		}
	}

	return Offer{
		OfferID:    offerID,
		SessionID:  query.SessionID,
		Products:   products,
		ExpiresAt:  time.Now().Add(15 * time.Minute),
		Protocol:   "nexusos-a2a/1.0",
		NegotiationURL: "/api/v1/agent/negotiate?session=" + query.SessionID,
	}
}

// ─── JSON Schema export helper ────────────────────────────────────────────────

// Schema returns the JSON schema for A2A commerce as a string.
func Schema() string {
	schema := map[string]interface{}{
		"$schema": "http://json-schema.org/draft-07/schema#",
		"title":   "NexusOS A2A Commerce Protocol",
		"version": "1.0",
		"types":   []string{"ProductQuery", "Offer", "CounterOffer", "Contract"},
	}
	b, _ := json.MarshalIndent(schema, "", "  ")
	return string(b)
}
