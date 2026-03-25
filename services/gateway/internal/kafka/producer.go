// ============================================================
// NexusOS — Kafka Producer
// File: services/gateway/internal/kafka/producer.go
// ============================================================
//
// WHAT IS KAFKA?
// Apache Kafka is a distributed event streaming platform.
// Think of it as a VERY FAST, DURABLE message queue.
//
// THE PATTERN: Producer → Topic → Consumer
//   Producer: this file — publishes messages TO a topic
//   Topic:   named channel (like "shopify.events", "pokemon.deals")
//            messages sit here until consumed
//   Consumer: the Python AI service — reads FROM the topic
//
// WHY KAFKA INSTEAD OF DIRECT HTTP CALLS?
// ┌──────────────────────────────────────────────────────────────────┐
// │  Direct Call (bad):                                              │
// │   Go → HTTP POST → Python AI service                            │
// │   If Python is slow (AI takes 30s), Go blocks.                  │
// │   If Python is down, request fails.                             │
// │   Shopify gets a 500, retries, creates duplicate events.        │
// │                                                                  │
// │  Kafka (good):                                                   │
// │   Go → Publish "shopify.events" → returns instantly             │
// │   Python reads at its own pace — even if it's restarting.      │
// │   Shopify gets 200 OK in <50ms.                                 │
// │   Python processes the event when it's ready.                   │
// │   If Python restarts, it picks up from where it left off.      │
// └──────────────────────────────────────────────────────────────────┘
//
// KEY KAFKA CONCEPTS:
//   Topic:     named channel for messages. "shopify.events" for Shopify webhooks.
//   Partition: a topic is split into N partitions for parallelism.
//              Messages with the same KEY always go to the same partition.
//              This preserves ORDER: all events from "mystore.myshopify.com"
//              arrive in the same order they were sent.
//   Offset:    position in a partition. Consumer tracks "I've read up to offset 42."
//              On restart, it resumes from offset 43.
//   Broker:    a Kafka server (Docker container: nexusos-kafka on port 9092)
//
// KAFKA IN DOCKER COMPOSE:
//   container: nexusos-kafka (confluentinc/cp-kafka:7.7.0)
//   port:      9092 (what apps connect to)
//              29092 (internal inter-broker communication)

// Package kafka provides the Kafka event producer for NexusOS.
// All event publishing in the Go gateway goes through here.
package kafka

import (
	// context: Go's way of passing deadlines, cancellation signals, and request-scoped
	// values through a call chain. API: context.WithTimeout(), context.Background()
	"context"
	// fmt: formatted string operations. fmt.Errorf() creates error values with messages.
	// %w: "wrap" an error — preserves the original error while adding context.
	"fmt"
	// log: Go's standard logging package. Writes to stderr by default.
	// log.Printf(): formatted print with automatic timestamp and newline.
	"log"
	// strings: string manipulation utilities. strings.Split("a,b,c", ",") → ["a","b","c"]
	"strings"
	// time: time values and durations. time.Second, time.Millisecond, time.Now()
	"time"

	// kafka-go: the Go Kafka client library. Installed via go.mod:
	//   require github.com/segmentio/kafka-go v0.4.47
	// This is NOT the official Confluent client — kafka-go is simpler and pure Go,
	// meaning it compiles cleanly without CGO (no C dependencies needed).
	"github.com/segmentio/kafka-go"
)

// Producer wraps kafka-go's Writer behind a clean interface.
//
// WHY WRAP IT?
// The rest of the codebase calls p.Publish(ctx, topic, key, value).
// If we ever need to switch Kafka client libraries, or add retry logic,
// or add metrics/tracing — we only change this file.
// The callers (webhook/handler.go, pokemon/handler.go) don't change at all.
// This is the "Adapter" or "Facade" design pattern.
type Producer struct {
	// writer is a pointer to the underlying kafka-go Writer.
	// kafka.Writer manages the TCP connections to Kafka brokers and
	// handles batching, retries, and partition selection internally.
	// The lowercase `writer` means it's unexported (private to this package).
	// External code CANNOT set `producer.writer = something_else`.
	// They can only use the Publish() and Close() public methods.
	writer *kafka.Writer
}

// NewProducer creates and configures a Kafka producer connected to the given broker(s).
//
// This is a CONSTRUCTOR FUNCTION — Go's idiomatic way to create initialized structs.
// Go doesn't have a `new` keyword like Java/C#. Instead:
//   producer := kafka.NewProducer("localhost:9092")
//
// Args:
//   brokers: comma-separated list of Kafka broker addresses.
//            e.g., "localhost:9092" (single broker, development)
//                  "kafka1:9092,kafka2:9092,kafka3:9092" (cluster, production)
//   The KAFKA_BROKERS env var from .env is passed in here from main.go.
func NewProducer(brokers string) *Producer {
	// strings.Split(s, sep) splits the string s by separator sep.
	// "kafka1:9092,kafka2:9092" → ["kafka1:9092", "kafka2:9092"]
	// If brokers is empty (""), Split returns [""] — one empty string.
	addrs := strings.Split(brokers, ",")
	if brokers == "" {
		// Fallback to localhost for local development
		// When no KAFKA_BROKERS is set, assume Kafka is on localhost:9092
		addrs = []string{"localhost:9092"}
	}

	// Create the Kafka Writer with all configuration.
	// `&kafka.Writer{...}` creates a Writer struct on the heap and returns a pointer.
	// In Go, `&` before a struct literal means "allocate on heap and return pointer to it."
	w := &kafka.Writer{
		// Addr: where the Kafka broker(s) are.
		// kafka.TCP(addrs...) creates a TCP address from the broker list.
		// The `...` "spreads" the slice: kafka.TCP("a", "b") instead of kafka.TCP(["a","b"]).
		Addr: kafka.TCP(addrs...),

		// Balancer: how to choose which partition to send a message to.
		// LeastBytes: send to the partition that has received the least data.
		// This balances load across partitions when volumes are unequal.
		// Alternative: kafka.Hash{} → same key always same partition (preserves order per key).
		// We use LeastBytes because our partition assignment is already handled by
		// providing explicit keys (same shop → same partition for ordering).
		Balancer: &kafka.LeastBytes{},

		// BatchTimeout: how long to accumulate messages before sending a batch.
		// 10ms means: "batch up to 10ms worth of messages before flushing to Kafka."
		// Lower = lower latency, slightly higher overhead per message.
		// 10ms is a good balance for webhook ingestion workloads.
		BatchTimeout: 10 * time.Millisecond,

		// Async: false = synchronous publishing.
		// Async=false means Publish() BLOCKS until Kafka acknowledges the message.
		// WHY NOT ASYNC? Because we need to know if Kafka accepted the message
		// before we return 200 to Shopify. If async and Kafka fails silently,
		// we've already told Shopify "success" and the event is lost.
		// Synchronous = safe. We return 500 to Shopify if Kafka fails → Shopify retries.
		Async: false,

		// MaxAttempts: retry up to 3 times if the initial write fails.
		// Network hiccups are common — 3 attempts handles most transient failures.
		// If all 3 fail, Publish() returns an error.
		MaxAttempts: 3,

		// WriteTimeout: maximum time to wait for Kafka to acknowledge a write.
		// If Kafka is overloaded and doesn't respond in 5 seconds, fail the call.
		// This prevents the webhook handler from hanging indefinitely.
		WriteTimeout: 5 * time.Second,
	}

	log.Printf("[kafka] Producer initialized, brokers=%s", brokers)

	// Return a pointer to our Producer wrapper struct.
	// `&Producer{writer: w}` = allocate Producer on heap, set its writer field, return pointer.
	return &Producer{writer: w}
}

// Publish sends a single message to the specified Kafka topic.
//
// This is the ONLY public method callers use. Simple interface:
//   err := producer.Publish(ctx, "shopify.events", "mystore.myshopify.com", eventJSON)
//
// Args:
//   ctx:   Request context — carries the deadline from the HTTP request.
//          If the HTTP request times out, ctx is cancelled, and WriteMessages
//          will stop retrying and return immediately with a context error.
//   topic: Which Kafka topic to publish to. Examples:
//          "shopify.events"        → all Shopify webhook events
//          "pokemon.deals"         → deal events from PokémonTool
//          "pokemon.trends"        → trend events from PokémonTool
//          "pokemon.price-alerts"  → price alert events from PokémonTool
//   key:   The partition routing key. Use shop domain or entity ID.
//          Messages with the same key → same Kafka partition → guaranteed ordering.
//          Example: all events for "mystore.myshopify.com" are ordered.
//   value: The raw bytes of the message body. Usually JSON-encoded struct.
//          Example: json.Marshal(KafkaEvent{...}) returns []byte which we pass here.
//
// Returns:
//   nil   = message successfully written and acknowledged by Kafka
//   error = Kafka unavailable, write failed after 3 attempts, or context cancelled
func (p *Producer) Publish(ctx context.Context, topic, key string, value []byte) error {
	// p.writer.WriteMessages() sends one or more messages to Kafka.
	// We send exactly ONE message per call (the current event).
	// For high-throughput systems, you'd batch many messages per call — but
	// for webhook handling, one-at-a-time is correct (we need to know each succeeded).
	err := p.writer.WriteMessages(ctx, kafka.Message{
		Topic: topic,       // which Kafka topic to publish to
		Key:   []byte(key), // partition key (string → bytes; Kafka messages are bytes)
		Value: value,       // message body (the JSON event bytes)
		Time:  time.Now(),  // message timestamp (stored in Kafka, useful for ordering/debugging)
	})
	if err != nil {
		// fmt.Errorf("...: %w", err) creates a new error that WRAPS the original.
		// The %w verb preserves the original error so callers can do:
		//   if errors.Is(err, kafka.ErrTimedOut) { ... }
		// Without %w, the original error type would be lost after wrapping.
		return fmt.Errorf("kafka publish failed for topic=%s key=%s: %w", topic, key, err)
	}
	return nil // nil in Go means "no error" (success)
}

// Close gracefully shuts down the Kafka producer.
//
// CALLED BY: main.go graceful shutdown handler.
// When the server receives SIGTERM (e.g., `docker stop` or `kill`), it:
//   1. Stops accepting new requests
//   2. Waits for in-flight requests to finish
//   3. Calls producer.Close() to flush pending Kafka batches
//   4. Exits
//
// writer.Close() flushes all buffered messages and closes TCP connections.
// Without this, messages in the 10ms BatchTimeout buffer could be lost on shutdown.
func (p *Producer) Close() error {
	return p.writer.Close()
}
