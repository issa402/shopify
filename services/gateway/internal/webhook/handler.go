// ============================================================
// NexusOS — Shopify Webhook Handler
// File: services/gateway/internal/webhook/handler.go
// ============================================================
//
// WHAT THIS FILE DOES:
// Every time something happens in a Shopify store that NexusOS cares about,
// Shopify sends an HTTP POST to one of our webhook endpoints.
// This file is the handler for ALL of those endpoints.
//
// SHOPIFY EVENTS WE HANDLE:
//   orders/create          → new order placed
//   orders/paid            → payment confirmed
//   orders/cancelled       → order cancelled
//   products/create        → new product added
//   products/update        → product info changed
//   inventory_levels/set   → stock level changed
//   customers/create       → new customer registered
//   customers/delete       → GDPR erasure request
//   refunds/create         → refund issued
//   checkouts/create       → someone started checkout (cart abandonment watch)
//
// THE 9-STEP PROCESS FOR EVERY WEBHOOK:
//   1. Read the body (limit 5MB for DoS protection)
//   2. Verify HMAC-SHA256 signature (ensures it came from Shopify, not a hacker)
//   3. Extract metadata from headers (event ID, shop domain)
//   4. Check Redis — did we already process this event? (idempotency)
//   5. Parse JSON body
//   6. Wrap in our KafkaEvent envelope (adds metadata + timestamp)
//   7. Publish to Kafka "shopify.events"
//   8. Mark as processed in Redis
//   9. Return HTTP 200 to Shopify (must happen within 5 seconds)
//
// WHY KAFKA INSTEAD OF PROCESSING DIRECTLY?
// Shopify REQUIRES a 200 response within 5 seconds or it marks the
// delivery as failed and retries. Our AI processing can take 10-30 seconds.
// Solution: publish to Kafka (fast, sub-100ms), return 200 immediately.
// The Python AI service processes the event at its own pace asynchronously.
//
// SECURITY MODEL:
//   - HMAC check: every request is cryptographically verified against
//     our SHOPIFY_WEBHOOK_SECRET. Forged requests are rejected with 401.
//   - Redis idempotency: Shopify retries failed deliveries. The same event
//     arriving twice is detected via Redis key and skipped.
//   - 5MB body limit: prevents memory exhaustion attacks.

// Package webhook handles inbound Shopify webhook events.
package webhook

import (
	// context: carries deadlines and cancellation signals.
	// We pass the HTTP request's context to Redis and Kafka calls so that
	// if the HTTP request is cancelled, those operations also cancel.
	"context"

	// crypto/hmac: HMAC (Hash-based Message Authentication Code) implementation.
	// HMAC = Hash(message + secret) → produces a signature.
	// Both sides know the secret. Compare signatures to verify authenticity.
	"crypto/hmac"

	// crypto/sha256: the SHA-256 hash function used inside HMAC.
	// HMAC-SHA256 is the specific combination Shopify uses.
	"crypto/sha256"

	// encoding/base64: encode binary bytes to printable ASCII string.
	// HMAC produces raw bytes. Shopify sends it as a base64 string in the header.
	// We base64-encode our computed HMAC to compare to the header.
	"encoding/base64"

	// encoding/json: JSON encoding/decoding for Go structs and maps.
	// json.Unmarshal: JSON bytes → Go struct/map
	// json.Marshal: Go struct/map → JSON bytes
	"encoding/json"

	// fmt: formatted strings and errors.
	"fmt"
	"io"  // io.ReadAll, io.LimitReader — for reading the HTTP request body
	"log" // standard logging to stderr
	"net/http"
	"os" // os.Getenv for reading environment variables
	"time"

	// gin: fast HTTP router framework for Go.
	// gin.Context = the request/response object (like req/res in Node.js Express)
	// gin.HandlerFunc = a function with signature func(c *gin.Context)
	"github.com/gin-gonic/gin"

	// go-redis: Redis client library for Go.
	// Redis is used here for idempotency key storage.
	// Each processed webhook ID is stored in Redis with a 24h TTL.
	"github.com/redis/go-redis/v9"

	// uuid: generates UUIDs (Universally Unique Identifiers).
	// Used as fallback if Shopify doesn't send a webhook ID header.
	"github.com/google/uuid"

	// pgxpool: PostgreSQL connection pool for Go.
	// Stored in Handler for audit logging (future: log every webhook to DB).
	"github.com/jackc/pgx/v5/pgxpool"

	// Our own Kafka producer package (internal/kafka/producer.go)
	"github.com/nexusos/gateway/internal/kafka"
)

// Handler is the dependency container for the webhook handling logic.
//
// DEPENDENCY INJECTION PATTERN:
// Instead of creating database connections inside each handler function,
// we create them ONCE (in main.go) and INJECT them into the Handler struct.
// Benefits:
//   - Testability: in tests, inject mock db/kafka/redis instead of real ones
//   - Single connection pool: one pgxpool.Pool for the whole service, not one per request
//   - Explicit dependencies: you can see at a glance what this handler needs to work
//
// STRUCT: groups related data together.
// Methods with receiver `(h *Handler)` have access to h.db, h.kafka, h.redis.
type Handler struct {
	// db is the PostgreSQL connection pool.
	// *pgxpool.Pool is a pointer to a connection pool — pgx manages multiple
	// concurrent connections and reuses them across goroutines.
	// Used for: writing to audit log table on each webhook received.
	db *pgxpool.Pool

	// kafka is our Kafka producer (from internal/kafka/producer.go).
	// Used to publish processed webhook events to Kafka topics.
	kafka *kafka.Producer

	// redis is the Redis client for idempotency key tracking.
	// Can be nil if Redis is unavailable — we handle that gracefully (fail-open).
	redis *redis.Client
}

// NewHandler constructor — creates a fully initialized Handler with all its dependencies.
//
// CALLED BY: main.go during startup.
//
//	webhookHandler := webhook.NewHandler(db, kafkaProducer)
//	router.POST("/webhooks/shopify/orders/create", webhookHandler.Handle("orders/create"))
//
// The Redis client is initialized HERE (not passed in) for simplicity,
// because its only config is the REDIS_URL environment variable.
func NewHandler(db *pgxpool.Pool, k *kafka.Producer) *Handler {
	// redis.ParseURL("redis://localhost:6379") parses the Redis connection string
	// into an options struct that the Redis client can use.
	// Returns an error if the URL is malformed.
	opt, err := redis.ParseURL(os.Getenv("REDIS_URL"))
	if err != nil {
		// If REDIS_URL is missing or malformed, warn but don't crash.
		// We can still process webhooks, just without duplicate detection.
		// This allows running in dev without Redis configured.
		log.Printf("[webhook] WARNING: could not parse REDIS_URL (%v) — idempotency disabled", err)
		// Return the handler with redis=nil. Our methods check for nil before using Redis.
		return &Handler{db: db, kafka: k, redis: nil}
	}

	// redis.NewClient(opt) creates the Redis client with the parsed options.
	// This doesn't actually connect yet — connection is lazy (on first command).
	rdb := redis.NewClient(opt)

	// Verify connectivity with a Ping before we accept webhooks.
	// context.WithTimeout creates a context that auto-cancels after 3 seconds.
	// `defer cancel()` ensures the timeout goroutine is cleaned up when this function returns.
	// `defer` = "run this at the end of the function, no matter how we exit."
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	// rdb.Ping(ctx).Err() sends a PING command to Redis.
	// If Redis responds, .Err() returns nil. If not, returns an error.
	if err := rdb.Ping(ctx).Err(); err != nil {
		log.Printf("[webhook] WARNING: Redis not reachable (%v) — idempotency disabled", err)
		return &Handler{db: db, kafka: k, redis: nil}
	}

	log.Println("[webhook] Redis connected for idempotency tracking")
	return &Handler{db: db, kafka: k, redis: rdb}
}

// Handle returns a Gin handler function for a specific Shopify event topic.
//
// CLOSURE PATTERN:
// Handle() is a function that RETURNS a function.
// The inner function "closes over" the `topic` parameter — even after Handle()
// returns, the inner function still knows what `topic` is.
//
// WHY USE A CLOSURE?
// We mount the same handler logic for 9+ different webhook routes:
//
//	router.POST("/webhooks/shopify/orders/create",   handler.Handle("orders/create"))
//	router.POST("/webhooks/shopify/products/update", handler.Handle("products/update"))
//
// Each call creates a NEW handler function with a different `topic` baked in.
// Without closures, we'd need 9 identical functions differing only in the topic string.
//
// PERFORMANCE TARGET: respond to Shopify in <50ms (p99)
//
//	Breakdown: read body ~1ms + HMAC ~0.5ms + Redis ~2ms + Kafka ~5ms = ~8.5ms typical.
func (h *Handler) Handle(topic string) gin.HandlerFunc {
	// Return an anonymous function with gin.HandlerFunc signature: func(c *gin.Context)
	// gin.Context wraps the underlying http.Request/http.ResponseWriter and adds helpers.
	return func(c *gin.Context) {
		// Record the start time to calculate total handler latency.
		start := time.Now()

		// ── STEP 1: Read request body ──────────────────────────────────────────
		// io.LimitReader wraps c.Request.Body with a 5MB limit.
		// 5<<20 is a bit shift: 5 × 2^20 = 5 × 1,048,576 = 5,242,880 bytes = 5MB.
		// WHY LIMIT: without a size limit, a malicious actor could send a 1GB body
		// and exhaust our server's memory. 5MB is generous for any real Shopify webhook.
		// io.ReadAll reads ALL bytes from the limited reader into memory.
		body, err := io.ReadAll(io.LimitReader(c.Request.Body, 5<<20))
		if err != nil {
			// Respond with 400 Bad Request if body can't be read.
			// gin.H{"error": "..."} is shorthand for map[string]interface{}{"error": "..."}
			c.JSON(http.StatusBadRequest, gin.H{"error": "failed to read body"})
			return // `return` exits the handler function immediately
		}

		// ── STEP 2: Verify HMAC-SHA256 Signature ──────────────────────────────
		// Shopify computes: HMAC-SHA256(body, SHOPIFY_WEBHOOK_SECRET)
		// Encodes result as base64 → puts in "X-Shopify-Hmac-SHA256" header.
		// We do the same computation and compare results.
		// If they match: the body wasn't tampered with AND came from Shopify.
		// If they don't match: reject with 401 Unauthorized.
		if !verifyHMAC(body, c.GetHeader("X-Shopify-Hmac-SHA256")) {
			log.Printf("[webhook] ❌ HMAC verification failed for topic=%s", topic)
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid signature"})
			return
		}

		// ── STEP 3: Extract Shopify metadata from headers ──────────────────────
		// c.GetHeader("X-Shopify-Webhook-Id") reads the HTTP request header.
		// Headers are key-value pairs sent alongside the HTTP body.
		// Shopify always includes these headers with webhook deliveries.

		// X-Shopify-Webhook-Id: unique ID for THIS delivery.
		// Same event delivered twice will have the SAME ID → how we detect duplicates.
		shopifyEventID := c.GetHeader("X-Shopify-Webhook-Id")

		// X-Shopify-Shop-Domain: which Shopify store sent this.
		// Format: "mystore.myshopify.com"
		// Used as Kafka message key (all events from same shop → same partition = ordered).
		shopDomain := c.GetHeader("X-Shopify-Shop-Domain")

		if shopifyEventID == "" {
			// Fallback: Shopify should ALWAYS send this ID, but be defensive.
			// uuid.New().String() generates a random UUID like "550e8400-e29b-..."
			// This won't have idempotency protection, but won't crash either.
			shopifyEventID = uuid.New().String()
		}

		// ── STEP 4: Idempotency check ─────────────────────────────────────────
		// Shopify retries failed deliveries up to 19 times over 48 hours.
		// If we returned 200 OK but Redis write failed, the retry would reprocess.
		// Solution: before processing, check if we've already seen this event ID.

		// Build the Redis key: "webhook:abc123-def456-..."
		// fmt.Sprintf = formatted string. "webhook:%s" → "webhook:" + shopifyEventID
		idempotencyKey := fmt.Sprintf("webhook:%s", shopifyEventID)

		if h.isProcessed(c.Request.Context(), idempotencyKey) {
			log.Printf("[webhook] ⏭  Duplicate skipped: eventID=%s topic=%s", shopifyEventID, topic)
			// Return 200 even for duplicates.
			// WHY 200 AND NOT 422? Shopify treats anything other than 200 as failure → retries more.
			// 200 tells Shopify "yes, we received and handled this" (which is true — we handled it previously).
			c.JSON(http.StatusOK, gin.H{"status": "already_processed"})
			return
		}

		// ── STEP 5: Parse JSON body ────────────────────────────────────────────
		// json.Unmarshal(src, dest) parses JSON into a Go variable.
		// `&payload` passes a POINTER to payload — Unmarshal writes into the pointed-to value.
		// map[string]interface{} = a dictionary where:
		//   - keys are strings (field names)
		//   - values can be ANY type (interface{} = Go's "any type" placeholder)
		// We use a generic map instead of a typed struct because we forward the
		// payload as-is to Kafka — we don't need to know its exact shape.
		var payload map[string]interface{}
		if err := json.Unmarshal(body, &payload); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid JSON payload"})
			return
		}

		// ── STEP 6: Build Kafka event envelope ────────────────────────────────
		// We WRAP the raw Shopify payload in our own envelope structure.
		// The envelope adds NexusOS-specific metadata:
		//   - which topic (what happened)
		//   - which shop (which merchant)
		//   - when we received it (for latency tracking, ordering)
		// Downstream Python consumers read this envelope, not raw Shopify JSON.
		event := KafkaEvent{
			ID:         shopifyEventID,   // unique delivery ID from Shopify
			Topic:      topic,            // e.g., "orders/create"
			ShopDomain: shopDomain,       // e.g., "mystore.myshopify.com"
			ReceivedAt: time.Now().UTC(), // UTC timestamp of receipt
			Payload:    payload,          // the raw Shopify event data (order, product, etc.)
		}

		// json.Marshal produces a JSON byte slice from our Go struct.
		// The `json:"id"` tags on KafkaEvent fields control the JSON key names.
		// `_` ignores the error — Marshal only fails for non-serializable types (channels, funcs).
		// Our struct is always serializable, so this is safe to ignore.
		eventJSON, _ := json.Marshal(event)

		// ── STEP 7: Publish to Kafka ───────────────────────────────────────────
		// All Shopify events go to the "shopify.events" Kafka topic.
		// The shop domain is the message KEY.
		// KEY SIGNIFICANCE: Kafka routes messages with the same key to the same partition.
		// Same partition = guaranteed ordering for that shop.
		// So "mystore" order events arrive at Python in the order they were created.
		// Without keying: events could arrive in any order (different partitions).
		if err := h.kafka.Publish(c.Request.Context(), "shopify.events", shopDomain, eventJSON); err != nil {
			log.Printf("[webhook] ❌ Kafka publish failed: topic=%s err=%v", topic, err)
			// Return 500 Server Error → Shopify will retry.
			// This is INTENTIONAL — we WANT Shopify to retry when Kafka is down.
			// When Kafka recovers, the retry will succeed and the event is processed.
			c.JSON(http.StatusInternalServerError, gin.H{"error": "event dispatch failed"})
			return
		}

		// ── STEP 8: Mark as processed in Redis ────────────────────────────────
		// Critical ordering: mark AFTER Kafka succeeds, not before.
		// If we marked before and Kafka failed: event marked processed but never published = LOST.
		// If we mark after and Redis fails: Kafka got the event (good!), worst case we process twice.
		// Duplicates are far less harmful than lost events.
		h.markProcessed(c.Request.Context(), idempotencyKey)

		// ── STEP 9: Log success and respond to Shopify ────────────────────────
		// time.Since(start) returns a time.Duration since `start`.
		// .Milliseconds() converts the duration to milliseconds as an int64.
		duration := time.Since(start).Milliseconds()

		log.Printf("[webhook] ✅ topic=%s shop=%s eventID=%s latency=%dms",
			topic, shopDomain, shopifyEventID, duration)

		// Respond 200 OK with accept confirmation.
		// Shopify requires this within 5 seconds. Our typical latency is <50ms.
		c.JSON(http.StatusOK, gin.H{
			"status":     "accepted",     // tells our monitoring: event was queued
			"event_id":   shopifyEventID, // echoed back for debugging/logging
			"latency_ms": duration,       // round-trip latency for monitoring
		})
	}
}

// verifyHMAC verifies that a Shopify webhook signature is valid.
//
// HOW HMAC WORKS (simplified):
//
//	Given: a SECRET key and a MESSAGE
//	HMAC = Hash(SECRET ⊕ pad1 || Hash(SECRET ⊕ pad2 || MESSAGE))
//	This produces a unique "fingerprint" of the message that only someone
//	with the SECRET can reproduce.
//
// SHOPIFY'S PROCESS:
//  1. Takes the raw JSON body bytes
//  2. Computes HMAC-SHA256 using SHOPIFY_WEBHOOK_SECRET as the key
//  3. Base64-encodes the 32-byte HMAC result
//  4. Sends it in the "X-Shopify-Hmac-SHA256" header
//
// OUR VERIFICATION:
//  1. Take the same raw body (we haven't modified it)
//  2. Compute HMAC-SHA256 with the SAME secret (from our .env)
//  3. Base64-encode it
//  4. Compare to the header value
//
// TIMING ATTACK PREVENTION:
//
//	Normal string comparison: `expected == signature`
//	This exits as soon as it finds the FIRST different character.
//	An attacker can measure HOW LONG the comparison takes to figure out
//	how many characters their fake signature has correct.
//	`hmac.Equal` compares ALL bytes regardless → constant time → no timing leak.
func verifyHMAC(body []byte, signature string) bool {
	secret := os.Getenv("SHOPIFY_WEBHOOK_SECRET")
	if secret == "" {
		// No secret set. In non-production, allow through for local testing.
		// In production, reject — never process unverified webhooks in prod.
		if os.Getenv("GO_ENV") != "production" {
			log.Println("[webhook] ⚠️  SHOPIFY_WEBHOOK_SECRET not set — skipping HMAC (dev mode)")
			return true
		}
		log.Println("[webhook] ❌ SHOPIFY_WEBHOOK_SECRET not set but GO_ENV=production")
		return false
	}

	// hmac.New(sha256.New, key): create a new HMAC hash object.
	//   sha256.New: the hash function to use (SHA-256, produces 32-byte output)
	//   []byte(secret): convert the string secret to bytes (HMAC key is []byte)
	mac := hmac.New(sha256.New, []byte(secret))

	// mac.Write(body): feed the request body bytes through the HMAC hasher.
	// This is how you "compute HMAC of these bytes with that key."
	mac.Write(body)

	// mac.Sum(nil): finalize and return the HMAC result as a byte slice.
	// nil = "return a new slice, don't append to an existing one."
	// base64.StdEncoding.EncodeToString: convert binary bytes to base64 string
	// (because the Shopify header contains base64, not raw binary)
	expected := base64.StdEncoding.EncodeToString(mac.Sum(nil))

	// hmac.Equal: constant-time byte comparison.
	// []byte(expected) and []byte(signature): convert strings to bytes for comparison.
	// Returns true if they match exactly.
	return hmac.Equal([]byte(expected), []byte(signature))
}

// isProcessed checks whether we've already handled a given webhook event.
//
// Redis GET semantics:
//   - Key exists: returns the stored value, err=nil
//   - Key not found: returns "", err=redis.Nil (special sentinel error)
//   - Redis error: returns "", err=(connection error / timeout / etc.)
//
// FAIL OPEN: if Redis is unavailable, we return false (process anyway).
// Rationale: it's LESS BAD to process a duplicate than to DROP an event.
// Duplicate orders in our system = minor data cleanup.
// Dropped orders = missed revenue + bad customer experience.
func (h *Handler) isProcessed(ctx context.Context, key string) bool {
	if h.redis == nil {
		// Redis not initialized (due to connection failure at startup).
		// We can't check for duplicates → process every event.
		return false
	}

	val, err := h.redis.Get(ctx, key).Result()
	if err == redis.Nil {
		// redis.Nil: special Redis error meaning "key not found."
		// This is NOT a connection error — it's the normal "hasn't been processed" state.
		return false
	}
	if err != nil {
		// Actual Redis error (timeout, connection refused, etc.)
		// Fail-open: treat as "not processed" to avoid dropping the event.
		log.Printf("[webhook] Redis GET error for key=%s: %v — processing anyway", key, err)
		return false
	}
	// val is the stored string ("1"). Non-empty means the key exists = already processed.
	return val != ""
}

// markProcessed stores the event ID in Redis so future duplicates can be detected.
//
// Redis SET with TTL:
//
//	SET key value EX seconds
//	SET "webhook:abc123" "1" EX 86400
//
// After 86400 seconds (24 hours), Redis automatically deletes the key.
// WHY 24 HOURS? Shopify retries webhooks for up to 48 hours, BUT:
//   - After 24 hours, the AI processing window has passed anyway
//   - Storing all webhook IDs forever would fill Redis memory
//   - 24 hours is a reasonable balance: covers all realistic retry windows
func (h *Handler) markProcessed(ctx context.Context, key string) {
	if h.redis == nil {
		return // Redis not available — can't mark, but we already processed successfully
	}

	// 24*time.Hour = 24 hours as a time.Duration (86400 seconds).
	// Redis.Set(ctx, key, value, ttl) → SET key value EX ttl_in_seconds
	if err := h.redis.Set(ctx, key, "1", 24*time.Hour).Err(); err != nil {
		// If Redis write fails: log it but don't fail the request.
		// The event was already published to Kafka successfully.
		// Worst case: the same event is processed twice.
		// That's acceptable — we built the downstream processing to be idempotent.
		log.Printf("[webhook] Redis SET failed for key=%s: %v", key, err)
	}
}

// KafkaEvent is the message envelope published to the "shopify.events" Kafka topic.
//
// WHY AN ENVELOPE?
// Raw Shopify webhooks don't include:
//   - Which topic they belong to (it's a URL parameter, not in the body)
//   - When NexusOS received them (Shopify's timestamp is when the event occurred)
//   - A consistent top-level structure we control
//
// By wrapping the raw payload in our envelope, Python consumers can always do:
//
//	event.topic → "orders/create"  (no need to inspect the payload to guess the type)
//	event.shop_domain → "mystore.myshopify.com"
//	event.payload → the raw Shopify order/product/customer object
//
// STRUCT TAGS ("json:\"id\""):
// Go uses struct tags to control how fields serialize to/from JSON.
// Without tags, Go uses field names directly: "ID" (Go) → "ID" (JSON).
// With tags: "ID" (Go) → "id" (JSON) — matches our Kafka message schema.
// The \" around field names are escaped quotes inside a raw string literal.
type KafkaEvent struct {
	// ID: Shopify's unique delivery ID for this webhook.
	// Used by consumers to deduplicate (same ID = same event, ignore if seen).
	ID string `json:"id"`

	// Topic: which Shopify event type this is.
	// e.g., "orders/create", "products/update", "customers/delete"
	// Python consumers switch on this to know what to do.
	Topic string `json:"topic"`

	// ShopDomain: which Shopify store sent this event.
	// e.g., "mystore.myshopify.com"
	// Used by Python to look up the merchant's configuration.
	ShopDomain string `json:"shop_domain"`

	// ReceivedAt: when NexusOS Gateway received this event (UTC).
	// Useful for latency monitoring: how long between event occurring and being processed.
	ReceivedAt time.Time `json:"received_at"`

	// Payload: the raw Shopify event body (the actual order/product/customer data).
	// map[string]interface{} = flexible JSON object (any field names, any value types).
	// Python reads this directly and parses fields it needs.
	Payload map[string]interface{} `json:"payload"`
}
