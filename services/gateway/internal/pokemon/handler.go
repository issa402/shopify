// ============================================================
// NexusOS Go Gateway — PokémonTool Inbound Event Handler
// File: services/gateway/internal/pokemon/handler.go
// ============================================================
//
// WHAT IS THIS FILE?
// The RECEIVING END of the PokémonTool ↔ NexusOS integration.
// It lives INSIDE NexusOS's Go Gateway and exposes three HTTP endpoints
// that PokémonTool's bridge.go sends events to.
//
// INTEGRATION DIAGRAM:
//   PokémonTool                     NexusOS
//   ─────────────                   ──────────────────────────────────
//   bridge.go calls                 THIS FILE receives
//   PushDeal()      →  HTTP POST /internal/pokemon/deal         →  Kafka "pokemon.deals"
//   PushTrend()     →  HTTP POST /internal/pokemon/trend        →  Kafka "pokemon.trends"
//   PushPriceAlert()→  HTTP POST /internal/pokemon/price-alert  →  Kafka "pokemon.price-alerts"
//                                                                          ↓
//                                             Python AI Service (pokemon_events.py consumer)
//
// THIS FILE'S THREE RESPONSIBILITIES:
//   1. AUTHENTICATE: Verify the X-Internal-Secret header to ensure the request
//      came from PokémonTool and not an external attacker spoofing events.
//   2. VALIDATE + PARSE: Check required fields. Parse JSON body into typed structs.
//   3. KAFKA PUBLISH: Put the event on the appropriate Kafka topic.
//      Return 200 OK immediately (PokémonTool has a 3-second timeout on these calls).
//
// WHY KAFKA INSTEAD OF DIRECTLY CALLING THE PYTHON AI SERVICE?
// ┌──────────────────────────────────────────────────────────────────────────┐
// │  WITHOUT KAFKA (direct HTTP call):                                       │
// │  PokémonTool → Gateway → HTTP POST → Python AI service                  │
// │  Problem: Python takes 30s to process (LLM reasoning).                  │
// │           PokémonTool waits 30s and times out. Event is lost.           │
// │                                                                          │
// │  WITH KAFKA (async queue):                                               │
// │  PokémonTool → Gateway → Publish to Kafka → Response in <100ms          │
// │  Python AI service reads from Kafka at its own pace.                    │
// │  Even if Python restarts, it picks up from its last Kafka offset.      │
// └──────────────────────────────────────────────────────────────────────────┘
//
// SECURITY MODEL FOR /internal/* ROUTES:
// These routes are protected by InternalAuthRequired() middleware.
// Only callers that know INTERNAL_SECRET can access them.
// INTERNAL_SECRET is a 32+ character random string shared between:
//   - NexusOS .env:         INTERNAL_SECRET=abc123...
//   - PokémonTool .env:     INTERNAL_SECRET=abc123...  (must be IDENTICAL)
// Generate: openssl rand -hex 32

// Package pokemon provides the inbound HTTP handlers for events from PokémonTool.
package pokemon

import (
	// encoding/json: JSON marshal/unmarshal.
	// We use it to:
	//   1. json.Unmarshal(): parse the incoming request body (JSON → Go struct)
	//   2. json.Marshal(): serialize event data into Kafka message bytes (Go map → JSON)
	"encoding/json"

	// io: provides io.ReadAll() and io.LimitReader().
	// io.LimitReader(r, n) wraps a reader with a maximum byte limit.
	// io.ReadAll() reads ALL bytes from a reader into memory.
	// Together: safely read request body with a size cap.
	"io"

	// log: standard logging to stderr with timestamp prefix.
	// log.Printf("[prefix] format", args...)
	"log"

	// net/http: HTTP status code constants.
	// http.StatusOK = 200, http.StatusBadRequest = 400,
	// http.StatusUnauthorized = 401, http.StatusForbidden = 403,
	// http.StatusInternalServerError = 500
	"net/http"

	// os: os.Getenv() for reading INTERNAL_SECRET and GO_ENV
	"os"

	// time: time.Now().UTC() for adding a "received_at" timestamp to Kafka events.
	// We add this to track latency: time between event creation and Kafka publish.
	"time"

	// gin: the HTTP router framework. gin.Context = request+response object.
	// gin.HandlerFunc = func(c *gin.Context) type alias for handler functions.
	// c.JSON() sends a JSON response. c.GetHeader() reads a request header.
	"github.com/gin-gonic/gin"

	// Our kafka producer package — provides Publish() method.
	"github.com/nexusos/gateway/internal/kafka"
)

// Handler is the dependency container for all three PokémonTool event handlers.
//
// WHY A STRUCT WITH A POINTER TO KAFKA?
// The kafka.Producer manages TCP connections to the Kafka broker.
// Creating a new producer per request would be expensive (new TCP connection each time).
// Instead: one Producer is created at startup and INJECTED into this Handler.
// All three handler methods share the same Producer instance.
// This is DEPENDENCY INJECTION — dependencies are passed in, not created internally.
type Handler struct {
	// kafka is the Kafka producer for publishing events.
	// Lowercase = unexported (private to this package).
	// The handler USES the kafka producer but doesn't OWN it (it's passed in, not created here).
	kafka *kafka.Producer
}

// NewHandler is the constructor for Handler.
//
// USAGE IN main.go:
//   kafkaProducer := kafka.NewProducer(os.Getenv("KAFKA_BROKERS"))
//   pokemonHandler := pokemon.NewHandler(kafkaProducer)
//   router.POST("/internal/pokemon/deal", pokemonHandler.ReceiveDeal)
//
// The `*kafka.Producer` parameter is a POINTER to the producer.
// In Go, large structs are passed as pointers to avoid copying the entire struct.
// Also, the producer has internal state (TCP connections) — we need to share
// the SAME instance, not a copy, hence pointer.
//
// Returns: *Handler (pointer to the newly created Handler struct)
func NewHandler(k *kafka.Producer) *Handler {
	return &Handler{kafka: k}
}


// ═══════════════════════════════════════════════════════════════════════════════
// PART 1: Inbound Event Structs
// ═══════════════════════════════════════════════════════════════════════════════
//
// These structs mirror the DealEvent, TrendEvent, PriceAlertEvent structs in
// Pokemon/server/nexusos/bridge.go.
//
// SYNCHRONIZATION REQUIREMENT:
// If PokémonTool adds a field to DealEvent.bridge.go, we MUST add the same
// field to InboundDeal here. Without the matching field:
//   - Go's json.Unmarshal silently IGNORES unknown JSON fields
//   - The field's data is lost (never makes it to Kafka)
//   - The Python AI service doesn't have the data it needs
//
// NAMING CONVENTION:
// Prefix "Inbound" distinguishes these from PokémonTool's outbound structs.
// InboundDeal (Go's name) ↔ DealEvent (PokémonTool's name) — same data, different name.
// The JSON field names (the string in backtick tags) MUST be identical on both sides.

// InboundDeal represents a deal event received from PokémonTool.
// A deal = a card selling ≥20% below its TCGplayer reference price.
//
// FIELD TYPES:
// float64 = 64-bit floating point decimal (Go's standard float type)
//           e.g., MarketPrice: 450.00, BestPrice: 320.00
// time.Time = Go's timestamp type. json.Unmarshal automatically parses
//             RFC 3339 strings like "2026-03-21T14:30:00Z" into time.Time.
type InboundDeal struct {
	CardName    string    `json:"card_name"`    // e.g., "Charizard Base Set Shadowless"
	MarketPrice float64   `json:"market_price"` // TCGplayer reference price (e.g., 450.00)
	BestPrice   float64   `json:"best_price"`   // cheapest eBay listing found (e.g., 320.00)
	SavingsPct  float64   `json:"savings_pct"`  // % below market: e.g., 28.9 = 28.9% off
	EbayURL     string    `json:"ebay_url"`     // direct link: "https://ebay.com/itm/..."
	DetectedAt  time.Time `json:"detected_at"`  // when PokémonTool found this deal (UTC)
}

// InboundTrend represents a significant price trend event from PokémonTool.
// Fired when a card's trending_score crosses ±50 (significant market movement).
type InboundTrend struct {
	CardName      string    `json:"card_name"`
	TrendLabel    string    `json:"trend_label"`    // "RISING" | "STABLE" | "FALLING"
	TrendingScore int       `json:"trending_score"` // -100 (falling fast) to +100 (rising fast)
	Price7dAgo    float64   `json:"price_7d_ago"`   // price 7 days ago (for context)
	PriceNow      float64   `json:"price_now"`      // current market price
	PctChange     float64   `json:"pct_change"`     // % change (signed: +15.3 or -8.7)
	DetectedAt    time.Time `json:"detected_at"`    // when this trend was computed (UTC)
}

// InboundPriceAlert represents a price threshold crossing event from PokémonTool.
// Fired when a user's watched card crosses above or below a set price.
type InboundPriceAlert struct {
	CardName    string    `json:"card_name"`
	NewPrice    float64   `json:"new_price"`    // current price after the threshold was crossed
	OldPrice    float64   `json:"old_price"`    // the price before this event (for context)
	PctChange   float64   `json:"pct_change"`   // % change from old_price to new_price
	Direction   string    `json:"direction"`    // "BELOW" (price fell below threshold) or "ABOVE"
	Marketplace string    `json:"marketplace"`  // "ebay" or "tcgplayer"
	ListingURL  string    `json:"listing_url"`  // direct URL to the specific listing (if any)
	TriggeredAt time.Time `json:"triggered_at"` // exact time the threshold was crossed (UTC)
}


// ═══════════════════════════════════════════════════════════════════════════════
// PART 2: HTTP Handler Methods
// ═══════════════════════════════════════════════════════════════════════════════

// ReceiveDeal handles POST /internal/pokemon/deal
//
// THE FULL PIPELINE FOR A DEAL EVENT:
//   1. PokémonTool's analytics engine scans eBay listings hourly
//   2. Finds Charizard listed at $320 (market price $450 = 28.9% discount)
//   3. bridge.go calls: bridge.PushDeal(deal) as a goroutine
//   4. Bridge POSTs to: POST /internal/pokemon/deal with JSON body
//   5. THIS FUNCTION validates, then publishes to Kafka "pokemon.deals"
//   6. Python consumer (pokemon_events.py) reads from Kafka
//   7. _handle_deal() runs LogisticsAgent then FinanceAgent
//   8. Creates a "Pending Approval" purchase order in the database
//   9. Merchant sees in dashboard: "Buy 1x Charizard at $320? ✅/❌"
//
// WHY RETURN 500 IF KAFKA FAILS?
// If we return 200 and Kafka publish failed: PokémonTool thinks we got the event.
// In reality the event was LOST. Returning 500 tells PokémonTool we failed.
// PokémonTool logs the error (doesn't retry, as bridge is fire-and-forget).
// But the deal will be re-detected on PokémonTool's next hourly scan anyway.
// This is "eventual consistency" — we might miss one cycle but never permanently lose data.
func (h *Handler) ReceiveDeal(c *gin.Context) {
	// Parse the JSON request body into InboundDeal struct.
	// readJSON is our helper below — reads with 1MB limit, then json.Unmarshal.
	var deal InboundDeal
	if err := readJSON(c, &deal); err != nil {
		// 400 Bad Request = the body was malformed JSON (parse error).
		// err.Error() extracts the Go error message as a string.
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid deal payload: " + err.Error()})
		return
	}

	// Business logic validation: are the critical fields present?
	// card_name == "": empty string (Go's zero value for string type).
	// best_price <= 0: price of zero or negative doesn't make sense.
	if deal.CardName == "" || deal.BestPrice <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "card_name and best_price are required"})
		return
	}

	// Build the Kafka event payload.
	// We use a generic map (map[string]interface{}) instead of a typed struct because:
	//   1. The Python consumer uses Python dicts (not typed structs)
	//   2. Maps are flexible — easy to add extra fields
	//   3. json.Marshal on a map produces clean JSON
	//
	// "received_at" is added here (not in bridge.go) because:
	//   - received_at = when NexusOS RECEIVED it
	//   - detected_at = when PokémonTool FOUND it
	//   - The difference between detected_at and received_at = network latency
	payload, _ := json.Marshal(map[string]interface{}{
		"event_type":   "pokemon.deal",     // label for the consumer's switch/case
		"card_name":    deal.CardName,
		"market_price": deal.MarketPrice,
		"best_price":   deal.BestPrice,
		"savings_pct":  deal.SavingsPct,
		"ebay_url":     deal.EbayURL,
		"detected_at":  deal.DetectedAt,    // when PokémonTool found it
		"received_at":  time.Now().UTC(),   // when we received it at NexusOS Gateway
	})

	// Publish to Kafka topic "pokemon.deals".
	// The Kafka KEY is deal.CardName (e.g., "Charizard Base Set Shadowless").
	// WHY USE CARD NAME AS KEY?
	// Kafka ensures messages with the SAME key go to the SAME partition.
	// All events about "Charizard Base Set Shadowless" are ordered in the same partition.
	// This means if we get deal → trend events for the same card,
	// they're processed in the order received (partition ordering guarantee).
	if err := h.kafka.Publish(c.Request.Context(), "pokemon.deals", deal.CardName, payload); err != nil {
		log.Printf("[pokemon-handler] ❌ Failed to publish deal to Kafka: %v", err)
		// 500 Internal Server Error: Kafka publish failed.
		// We return 500 so PokémonTool knows the event wasn't stored.
		// The Go Gateway logs this for alerting/monitoring.
		c.JSON(http.StatusInternalServerError, gin.H{"error": "event dispatch failed"})
		return
	}

	log.Printf("[pokemon-handler] ✅ Deal received and queued: %s at $%.2f (%.1f%% below market)",
		deal.CardName, deal.BestPrice, deal.SavingsPct)

	// Return 200 OK immediately.
	// PokémonTool's bridge.go has a 3-second timeout on these calls.
	// We respond in <100ms (validation + Kafka write), well within the timeout.
	c.JSON(http.StatusOK, gin.H{
		"status":     "accepted",
		"event_type": "pokemon.deal",
	})
}

// ReceiveTrend handles POST /internal/pokemon/trend
//
// WHAT TRIGGERS THIS:
// PokémonTool's analytics engine runs its trending scorer hourly.
// When a card's trending_score crosses ±50 (significant move), it calls PushTrend().
//
// WHAT NEXUSOS DOES WITH A TREND EVENT:
// Published to Kafka "pokemon.trends". Python consumer's _handle_trend() reads it.
// FinanceAgent (the manager agent) checks:
//   RISING card: Do we list this? If yes → raise price. If no → suggest adding to catalog?
//   FALLING card: Do we have inventory? If yes → flash sale. If no → halt restock orders.
// All Shopify price changes >$50 are queued for merchant approval first.
func (h *Handler) ReceiveTrend(c *gin.Context) {
	var trend InboundTrend
	if err := readJSON(c, &trend); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid trend payload: " + err.Error()})
		return
	}

	if trend.CardName == "" || trend.TrendLabel == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "card_name and trend_label are required"})
		return
	}

	// Add event_type label + received_at timestamp to the Kafka message.
	// The Python consumer reads event_type to confirm which topic this came from.
	payload, _ := json.Marshal(map[string]interface{}{
		"event_type":     "pokemon.trend",
		"card_name":      trend.CardName,
		"trend_label":    trend.TrendLabel,    // "RISING" | "STABLE" | "FALLING"
		"trending_score": trend.TrendingScore, // the magnitude: +75, -50, etc.
		"price_7d_ago":   trend.Price7dAgo,
		"price_now":      trend.PriceNow,
		"pct_change":     trend.PctChange,     // e.g., +15.3 (15.3% rise over 7 days)
		"detected_at":    trend.DetectedAt,
		"received_at":    time.Now().UTC(),
	})

	if err := h.kafka.Publish(c.Request.Context(), "pokemon.trends", trend.CardName, payload); err != nil {
		log.Printf("[pokemon-handler] ❌ Failed to publish trend to Kafka: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "event dispatch failed"})
		return
	}

	log.Printf("[pokemon-handler] ✅ Trend received: %s → %s (score: %d, Δ%.1f%%)",
		trend.CardName, trend.TrendLabel, trend.TrendingScore, trend.PctChange)

	c.JSON(http.StatusOK, gin.H{"status": "accepted", "event_type": "pokemon.trend"})
}

// ReceivePriceAlert handles POST /internal/pokemon/price-alert
//
// WHAT TRIGGERS THIS:
// When notification_worker.go creates a user-facing price alert,
// it ALSO pushes that event to NexusOS via bridge.PushPriceAlert().
// This gives NexusOS AI agents awareness of price threshold crossings.
//
// WHAT NEXUSOS DOES:
// Published to "pokemon.price-alerts". Python consumer's _handle_price_alert() reads it.
// If the price fell 15%+: reuse the deal evaluation pipeline.
// Always: refresh the negotiation engine's price cache for any in-progress A2A deals.
func (h *Handler) ReceivePriceAlert(c *gin.Context) {
	var alert InboundPriceAlert
	if err := readJSON(c, &alert); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid price alert payload: " + err.Error()})
		return
	}

	if alert.CardName == "" || alert.NewPrice <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "card_name and new_price are required"})
		return
	}

	payload, _ := json.Marshal(map[string]interface{}{
		"event_type":   "pokemon.price_alert",
		"card_name":    alert.CardName,
		"new_price":    alert.NewPrice,     // the new (current) market price
		"old_price":    alert.OldPrice,     // the previous reference price
		"pct_change":   alert.PctChange,    // signed % change (negative = price fell)
		"direction":    alert.Direction,    // "BELOW" or "ABOVE" the alert threshold
		"marketplace":  alert.Marketplace,  // "ebay" or "tcgplayer"
		"listing_url":  alert.ListingURL,   // direct link to the listing (if available)
		"triggered_at": alert.TriggeredAt,  // exact time threshold was crossed
		"received_at":  time.Now().UTC(),   // when NexusOS Gateway received this
	})

	if err := h.kafka.Publish(c.Request.Context(), "pokemon.price-alerts", alert.CardName, payload); err != nil {
		log.Printf("[pokemon-handler] ❌ Failed to publish price-alert to Kafka: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "event dispatch failed"})
		return
	}

	log.Printf("[pokemon-handler] ✅ Price alert received: %s %s to $%.2f (%.1f%% change)",
		alert.CardName, alert.Direction, alert.NewPrice, alert.PctChange)

	c.JSON(http.StatusOK, gin.H{"status": "accepted", "event_type": "pokemon.price_alert"})
}


// ═══════════════════════════════════════════════════════════════════════════════
// PART 3: Internal Authentication Middleware
// ═══════════════════════════════════════════════════════════════════════════════

// InternalAuthRequired returns Gin middleware that validates the X-Internal-Secret header.
//
// WHAT IS GIN MIDDLEWARE?
// Middleware runs BEFORE the actual handler function.
// You can chain multiple middleware: auth → logging → rateLimiting → handler.
// Each middleware calls c.Next() to pass control to the next thing in the chain.
// If middleware calls c.AbortWithStatusJSON(), it STOPS the chain — the handler never runs.
//
// USAGE IN main.go:
//   internal := router.Group("/internal")
//   internal.Use(pokemon.InternalAuthRequired())  // applies to ALL /internal/* routes
//   {
//       internal.POST("/pokemon/deal",        pokemonHandler.ReceiveDeal)
//       internal.POST("/pokemon/trend",       pokemonHandler.ReceiveTrend)
//       internal.POST("/pokemon/price-alert", pokemonHandler.ReceivePriceAlert)
//   }
//
// WHY NOT JWT FOR INTERNAL AUTH?
// JWT (JSON Web Tokens) are designed for human users authenticating to services.
// They involve:
//   - Token generation + signing
//   - Token expiry management
//   - Refresh token workflow
// For SERVICE-TO-SERVICE auth where both services share a secret:
//   - Shared secret in .env is simpler, faster, and equally secure
//   - No token expiry to manage
//   - Just: send the secret → check the secret → allow or deny
// This is essentially "API key" authentication, the standard for internal APIs.
//
// WHY CLOSURE (returns a function)?
// Same reason as webhook/handler.go's Handle() — Gin middleware must have the
// signature func(c *gin.Context). But we want our function to "remember" the
// INTERNAL_SECRET value. A closure captures variables from the enclosing scope.
// If we read INTERNAL_SECRET in the returned function directly, we'd need to
// re-read os.Getenv on EVERY request. With the closure approach, we could
// read it once at startup (not done here to allow hot config, but it's an option).
func InternalAuthRequired() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Read INTERNAL_SECRET from environment on each request.
		// This allows updating the secret without restarting (live config update).
		// In high-traffic production: cache this at startup for performance.
		secret := os.Getenv("INTERNAL_SECRET")

		if secret == "" {
			// Secret not configured.
			// In non-production (development, testing): allow requests through with just a warning.
			// Go's convention for checking environment: os.Getenv("GO_ENV") == "production"
			if os.Getenv("GO_ENV") == "production" {
				// In production: NEVER allow unconfigured auth. Reject with 500.
				// A 500 here signals a server configuration error, not an auth error.
				// (The admin needs to fix this, not the caller.)
				c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{
					"error": "INTERNAL_SECRET not configured on NexusOS Gateway",
				})
				return
			}
			// Dev mode: warn but proceed. Allows local testing without secrets.
			log.Println("[internal-auth] ⚠️  INTERNAL_SECRET not set — bypassing auth (dev mode)")
			c.Next() // pass control to the actual handler
			return
		}

		// c.GetHeader("X-Internal-Secret"): read the authentication header from the request.
		// gin.Context.GetHeader: like c.Request.Header.Get() but cleaner API.
		incoming := c.GetHeader("X-Internal-Secret")

		if incoming == "" {
			// No secret provided at all. Likely a misconfigured caller or an external probe.
			// 401 Unauthorized: "you need to authenticate to access this resource."
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
				"error": "X-Internal-Secret header required for internal routes",
			})
			return
		}

		// Compare the incoming secret to our configured secret.
		// len(incoming) != len(secret): different lengths → definitely different → reject.
		// incoming != secret: content mismatch → reject.
		//
		// NOTE ON TIMING ATTACKS:
		// This string comparison (incoming != secret) is NOT constant-time.
		// Go's string != operator short-circuits at the first differing byte.
		// A true timing-safe comparison uses hmac.Equal() (as in webhook/handler.go).
		// For internal service-to-service auth, timing attacks are much less of a concern
		// than for public-facing auth endpoints. This is acceptable for our use case.
		// If you want paranoid security: use hmac.Equal([]byte(incoming), []byte(secret)).
		if len(incoming) != len(secret) || incoming != secret {
			// Log the client IP for blocking/alerting on repeated failures.
			// c.ClientIP(): extracts the real client IP, respecting X-Forwarded-For headers.
			log.Printf("[internal-auth] ❌ Invalid internal secret from IP: %s", c.ClientIP())
			// 403 Forbidden: "you're authenticated but not allowed here" — or in this case,
			// "the credential you provided is wrong."
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
				"error": "invalid internal secret",
			})
			return
		}

		// c.Next(): passes control to the next middleware/handler in the chain.
		// Without this: the chain stops here even on success.
		c.Next()
	}
}


// ═══════════════════════════════════════════════════════════════════════════════
// PART 4: Request Body Helper
// ═══════════════════════════════════════════════════════════════════════════════

// readJSON reads and JSON-decodes the HTTP request body into a target struct.
//
// WHY NOT USE gin's c.ShouldBindJSON()?
// gin has c.ShouldBindJSON(&target) which does the same thing.
// We use our own helper for two reasons:
//   1. Explicit 1MB body size limit (DoS protection)
//      c.ShouldBindJSON() uses the default body reader without a size cap.
//   2. Explicit control over error messages (readJSON returns the raw io error,
//      which is better for debugging than gin's generic binding errors)
//
// WHY 1MB LIMIT (vs webhook handler's 5MB)?
// Pokemon events are small structured JSON (card names, prices, URLs).
// A 1MB limit is more than sufficient for the largest possible event.
// Keeping limits tight prevents abuse.
//
// FUNCTION SIGNATURE:
//   readJSON(c *gin.Context, target interface{}) error
//   - c: the gin request context (to read c.Request.Body from)
//   - target: a pointer to the struct to write into (e.g., &deal for *InboundDeal)
//     `interface{}`: Go's "any type" — accepts any pointer
//   - Returns: nil on success, error on parse failure
func readJSON(c *gin.Context, target interface{}) error {
	// io.LimitReader(r, n) wraps an io.Reader with a maximum read limit.
	// c.Request.Body: the raw HTTP request body as an io.Reader (byte stream).
	// 1<<20 = 1 × 2^20 = 1,048,576 bytes = 1 MB.
	// io.ReadAll() reads ALL bytes from the limited reader into memory.
	body, err := io.ReadAll(io.LimitReader(c.Request.Body, 1<<20))
	if err != nil {
		return err // return the io.ReadAll error (network read error, etc.)
	}

	// json.Unmarshal(src, dst): parse JSON bytes into the Go struct.
	// `target` is a pointer (interface{} containing a *InboundDeal or similar).
	// json.Unmarshal writes the parsed values into the struct through the pointer.
	// Returns nil on success, error on:
	//   - Invalid JSON syntax
	//   - Type mismatch (JSON string into a float64 field, etc.)
	return json.Unmarshal(body, target)
}
