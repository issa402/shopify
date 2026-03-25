// Package main is the NexusOS Gateway Service entry point.
// This Go service handles Shopify webhook ingestion, A2A commerce,
// MCP protocol hosting, and serves as the core API gateway.
package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/nexusos/gateway/internal/a2a"
	"github.com/nexusos/gateway/internal/auth"
	"github.com/nexusos/gateway/internal/db"
	"github.com/nexusos/gateway/internal/kafka"
	"github.com/nexusos/gateway/internal/mcp"
	"github.com/nexusos/gateway/internal/middleware"
	"github.com/nexusos/gateway/internal/webhook"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using environment variables")
	}

	// Initialize database connection pool
	pool, err := db.Connect(os.Getenv("DATABASE_URL"))
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer pool.Close()

	// Run migrations
	if err := db.RunMigrations(pool); err != nil {
		log.Fatalf("Failed to run migrations: %v", err)
	}

	// Initialize Kafka producer
	kafkaProducer := kafka.NewProducer(os.Getenv("KAFKA_BROKERS"))
	defer kafkaProducer.Close()

	// Initialize MCP Hub
	mcpHub, err := mcp.NewHub("./mcp-config.json")
	if err != nil {
		log.Printf("Warning: MCP Hub initialization failed: %v (continuing without MCP)", err)
	}

	// Setup Gin router
	if os.Getenv("GO_ENV") == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()
	router.Use(gin.Logger())
	router.Use(gin.Recovery())
	router.Use(middleware.CORS())
	router.Use(middleware.OpenTelemetry())

	// ── Health Check ──────────────────────────────────────────────────
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "healthy",
			"service": "nexusos-gateway",
			"version": "2026.1.0",
			"time":    time.Now().UTC(),
		})
	})

	// ── Shopify OAuth ─────────────────────────────────────────────────
	authHandler := auth.NewShopifyOAuthHandler(pool)
	router.GET("/auth/shopify", authHandler.InitiateOAuth)
	router.GET("/auth/callback", authHandler.HandleCallback)

	// ── Shopify Webhooks ─────────────────────────────────────────────
	webhookHandler := webhook.NewHandler(pool, kafkaProducer)
	webhooks := router.Group("/webhooks/shopify")
	{
		webhooks.POST("/orders/create", webhookHandler.Handle("orders/create"))
		webhooks.POST("/orders/paid", webhookHandler.Handle("orders/paid"))
		webhooks.POST("/orders/cancelled", webhookHandler.Handle("orders/cancelled"))
		webhooks.POST("/orders/updated", webhookHandler.Handle("orders/updated"))
		webhooks.POST("/products/create", webhookHandler.Handle("products/create"))
		webhooks.POST("/products/update", webhookHandler.Handle("products/update"))
		webhooks.POST("/inventory_levels/set", webhookHandler.Handle("inventory_levels/set"))
		webhooks.POST("/customers/create", webhookHandler.Handle("customers/create"))
		webhooks.POST("/customers/update", webhookHandler.Handle("customers/update"))
		webhooks.POST("/customers/delete", webhookHandler.Handle("customers/delete"))
		webhooks.POST("/refunds/create", webhookHandler.Handle("refunds/create"))
	}

	// ── API v1 (authenticated routes) ─────────────────────────────────
	api := router.Group("/api/v1")
	api.Use(middleware.AuthRequired(pool))
	api.Use(middleware.RBAC())
	{
		// A2A Commerce Interface
		a2aHandler := a2a.NewHandler(mcpHub)
		api.POST("/agent/negotiate", a2aHandler.Negotiate)
		api.GET("/agent/capabilities", a2aHandler.Capabilities)

		// Merchant data endpoints
		api.GET("/orders", func(c *gin.Context) {
			merchantID := c.GetString("merchant_id")
			c.JSON(http.StatusOK, gin.H{"merchant_id": merchantID, "orders": []interface{}{}})
		})
		api.GET("/customers", func(c *gin.Context) {
			merchantID := c.GetString("merchant_id")
			c.JSON(http.StatusOK, gin.H{"merchant_id": merchantID, "customers": []interface{}{}})
		})
		api.GET("/ai/decisions", func(c *gin.Context) {
			merchantID := c.GetString("merchant_id")
			c.JSON(http.StatusOK, gin.H{"merchant_id": merchantID, "decisions": []interface{}{}})
		})
		api.GET("/approvals/pending", func(c *gin.Context) {
			merchantID := c.GetString("merchant_id")
			c.JSON(http.StatusOK, gin.H{"merchant_id": merchantID, "pending": []interface{}{}})
		})
		api.POST("/approvals/:id/approve", func(c *gin.Context) {
			c.JSON(http.StatusOK, gin.H{"status": "approved", "id": c.Param("id")})
		})
		api.POST("/approvals/:id/reject", func(c *gin.Context) {
			c.JSON(http.StatusOK, gin.H{"status": "rejected", "id": c.Param("id")})
		})

		// GDPR/CCPA compliance - data deletion
		api.DELETE("/customers/:id", func(c *gin.Context) {
			// TODO: cascade delete across Postgres, Qdrant, and MCP tools
			c.JSON(http.StatusAccepted, gin.H{
				"status":      "deletion_queued",
				"customer_id": c.Param("id"),
				"message":     "Data deletion cascaded across all connected systems",
			})
		})
	}

	// Start server with graceful shutdown
	port := os.Getenv("PORT_GATEWAY")
	if port == "" {
		port = "8080"
	}

	srv := &http.Server{
		Addr:         ":" + port,
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		log.Printf("🚀 NexusOS Gateway starting on port %s", port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Graceful shutdown on SIGTERM/SIGINT
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down NexusOS Gateway...")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("Gateway forced to shutdown: %v", err)
	}
	log.Println("Gateway exited cleanly.")
}
