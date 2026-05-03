// Package middleware provides Gin middleware for NexusOS Gateway.
package middleware

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
)

// Role constants
const (
	RoleOwner   = "owner"
	RoleAdmin   = "admin"
	RoleSupport = "support"
	RoleViewer  = "viewer"
)

// routePermissions maps HTTP method + path prefix to minimum required role.
var routePermissions = map[string]string{
	"DELETE:/api/v1/customers":     RoleAdmin,  // GDPR deletion requires admin
	"POST:/api/v1/approvals":       RoleAdmin,  // approve/reject requires admin
	"GET:/api/v1/ai/decisions":     RoleViewer, // anyone can view AI logs
	"GET:/api/v1/orders":           RoleViewer,
	"GET:/api/v1/customers":        RoleViewer,
	"POST:/api/v1/agent/negotiate": RoleOwner, // A2A only for store owners
}

// Claims is the NexusOS JWT payload.
type Claims struct {
	MerchantID string `json:"merchant_id"`
	ShopDomain string `json:"shop_domain"`
	Role       string `json:"role"`
	jwt.RegisteredClaims
}

// AuthRequired validates the Bearer JWT token on protected routes.
func AuthRequired(db *pgxpool.Pool) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "authorization header required"})
			return
		}

		parts := strings.SplitN(authHeader, " ", 2)
		if len(parts) != 2 || parts[0] != "Bearer" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "invalid authorization format"})
			return
		}

		tokenStr := parts[1]
		claims := &Claims{}
		secret := os.Getenv("JWT_SECRET")

		token, err := jwt.ParseWithClaims(tokenStr, claims, func(t *jwt.Token) (interface{}, error) {
			return []byte(secret), nil
		})

		if err != nil || !token.Valid {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "invalid or expired token"})
			return
		}

		// Set merchant context for RLS
		c.Set("merchant_id", claims.MerchantID)
		c.Set("shop_domain", claims.ShopDomain)
		c.Set("role", claims.Role)

		// Set Postgres RLS session variable for this request
		// This is done at the DB query layer, not here
		c.Next()
	}
}

// RBAC enforces role-based access control on each route.
func RBAC() gin.HandlerFunc {
	return func(c *gin.Context) {
		role := c.GetString("role")
		if role == "" {
			c.Next()
			return
		}

		routeKey := c.Request.Method + ":" + c.FullPath()
		requiredRole, exists := routePermissions[routeKey]
		if !exists {
			c.Next()
			return
		}

		if !hasPermission(role, requiredRole) {
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
				"error":         "insufficient_permissions",
				"required_role": requiredRole,
				"your_role":     role,
			})
			return
		}

		c.Next()
	}
}

// hasPermission returns true if the subject role satisfies the required role.
func hasPermission(subjectRole, requiredRole string) bool {
	hierarchy := map[string]int{
		RoleOwner:   4,
		RoleAdmin:   3,
		RoleSupport: 2,
		RoleViewer:  1,
	}
	return hierarchy[subjectRole] >= hierarchy[requiredRole]
}

// CORS adds permissive CORS headers for development. Tighten for production.
func CORS() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Agent-Type")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}
		c.Next()
	}
}

// OpenTelemetry attaches trace context to each request.
func OpenTelemetry() gin.HandlerFunc {
	return func(c *gin.Context) {
		// TODO: extract/inject OTel span context from incoming requests
		// tracer := otel.Tracer("nexusos-gateway")
		// ctx, span := tracer.Start(c.Request.Context(), c.FullPath())
		// defer span.End()
		// c.Request = c.Request.WithContext(ctx)
		c.Next()
	}
}
