// Package auth implements Shopify OAuth 2.0 for app installation.
//
// HOW SHOPIFY OAUTH WORKS (like signing in with Google but for stores):
//
//  1. Merchant clicks "Add App" on Shopify's app store.
//  2. Shopify redirects them to: GET /auth/shopify?shop=mystore.myshopify.com
//  3. We generate a random "state" token (CSRF protection) and store it in a cookie.
//  4. We redirect the merchant to Shopify's authorization page, telling Shopify:
//     - Which app we are (SHOPIFY_CLIENT_ID)
//     - What permissions we need (orders, products, customers, inventory)
//     - Where to send them back when done (SHOPIFY_APP_URL/auth/callback)
//     - Our CSRF state token
//  5. Merchant clicks "Install" on Shopify's page.
//  6. Shopify redirects back to: GET /auth/callback?shop=...&code=...&state=...
//  7. We verify the state matches our cookie (CSRF check).
//  8. We swap the temporary "code" for a permanent "access_token" by calling Shopify's API.
//  9. We store the access_token in our database next to the merchant.
//  10. From now on, when we need to call the Shopify Admin API for this merchant,
//      we use their stored access_token.
package auth

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgxpool"
)

// ShopifyOAuthHandler holds the database pool so it can save merchant access tokens.
// We inject the DB pool through the constructor (NewShopifyOAuthHandler) because:
//   - It makes testing easier (you can pass a mock DB in tests)
//   - It avoids global variables (which are hard to test and can cause race conditions)
type ShopifyOAuthHandler struct {
	db *pgxpool.Pool
}

// NewShopifyOAuthHandler is the constructor function.
// You call this once at startup in main.go:
//
//	authHandler := auth.NewShopifyOAuthHandler(pool)
func NewShopifyOAuthHandler(db *pgxpool.Pool) *ShopifyOAuthHandler {
	return &ShopifyOAuthHandler{db: db}
}

// InitiateOAuth starts the OAuth flow by redirecting to Shopify's authorization page.
// Called by: GET /auth/shopify?shop=merchant.myshopify.com
//
// The merchant arrives here when they click "Install" from the Shopify app listing.
func (h *ShopifyOAuthHandler) InitiateOAuth(c *gin.Context) {
	// Get the shop domain from the query string.
	// e.g. "mystore.myshopify.com" — every Shopify store has a unique .myshopify.com subdomain
	shop := c.Query("shop")
	if shop == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "shop parameter is required"})
		return
	}

	// Generate a random CSRF state token.
	// CSRF (Cross-Site Request Forgery) protection: we generate a random string,
	// store it in a cookie, and include it in the URL we send to Shopify.
	// When Shopify sends the merchant back, they include this token in the URL.
	// We verify it matches what's in the cookie. This prevents attackers from
	// crafting fake callback URLs to install the app on stores they don't own.
	state, err := generateState()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to generate state"})
		return
	}

	// Store the state in a secure HTTP-only cookie (TTL: 10 minutes).
	// "HttpOnly" means JavaScript can't read this cookie (XSS protection).
	// "Secure" means it's only sent over HTTPS (we set it to true always).
	// 600 seconds = 10 minutes — enough time for the merchant to click Install.
	c.SetCookie("shopify_oauth_state", state, 600, "/", "", false, true)

	// These are the Shopify permission scopes we're requesting.
	// The merchant will see a list like "This app wants to: read your orders, edit products, etc."
	scopes := "read_orders,write_orders,read_customers,write_customers,read_products,write_products,read_inventory,write_inventory"

	redirectURI := os.Getenv("SHOPIFY_APP_URL") + "/auth/callback"
	clientID := os.Getenv("SHOPIFY_CLIENT_ID")

	// Build the Shopify authorization URL.
	// We use url.QueryEscape to safely encode special characters in the URL parameters.
	authURL := fmt.Sprintf(
		"https://%s/admin/oauth/authorize?client_id=%s&scope=%s&redirect_uri=%s&state=%s",
		shop,
		url.QueryEscape(clientID),
		url.QueryEscape(scopes),
		url.QueryEscape(redirectURI),
		url.QueryEscape(state),
	)

	log.Printf("[oauth] Redirecting shop=%s to Shopify authorization", shop)

	// 302 redirect — the browser goes to Shopify's page.
	c.Redirect(http.StatusFound, authURL)
}

// HandleCallback processes the OAuth callback from Shopify.
// Called by: GET /auth/callback?shop=...&code=...&state=...
//
// Shopify redirects the merchant back here after they click "Install".
// The "code" parameter is a short-lived authorization code we swap for an access token.
func (h *ShopifyOAuthHandler) HandleCallback(c *gin.Context) {
	shop := c.Query("shop")
	code := c.Query("code")
	state := c.Query("state") // the random token Shopify echoes back to us

	// ── CSRF Validation ───────────────────────────────────────────────────────
	// Retrieve the state we stored in the cookie during InitiateOAuth.
	// Compare it with what Shopify sent back. They must match.
	// If they don't match, this callback was NOT initiated by our app — reject it.
	cookieState, err := c.Cookie("shopify_oauth_state")
	if err != nil || cookieState != state {
		log.Printf("[oauth] CSRF check failed for shop=%s: cookie=%q url=%q", shop, cookieState, state)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid state — possible CSRF attack"})
		return
	}

	if shop == "" || code == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "missing shop or code parameter"})
		return
	}

	// ── Exchange Code for Access Token ────────────────────────────────────────
	// The "code" Shopify gave us is temporary (valid for ~1 minute).
	// We call Shopify's token endpoint to swap it for a permanent access_token.
	// This access_token is what we use to call the Shopify Admin API going forward.
	accessToken, scope, err := exchangeCodeForToken(shop, code)
	if err != nil {
		log.Printf("[oauth] Token exchange failed for shop=%s: %v", shop, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "token exchange failed"})
		return
	}

	// ── Store Merchant in Database ────────────────────────────────────────────
	// We use an "upsert" (INSERT ... ON CONFLICT DO UPDATE) so that:
	//   - First install: creates a new merchant row
	//   - Reinstall: updates the existing row with the new access_token
	//
	// The access_token is stored in plaintext here. In production you might
	// want to encrypt it. For now, database access control + RLS protects it.
	ctx, cancel := context.WithTimeout(c.Request.Context(), 5*time.Second)
	defer cancel()

	_, err = h.db.Exec(ctx, `
		INSERT INTO merchants (shop_domain, access_token, scope)
		VALUES ($1, $2, $3)
		ON CONFLICT (shop_domain) DO UPDATE
		SET access_token = $2,
		    scope        = $3,
		    is_active    = TRUE,
		    updated_at   = NOW()
	`, shop, accessToken, scope)
	if err != nil {
		log.Printf("[oauth] DB upsert failed for shop=%s: %v", shop, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to store merchant"})
		return
	}

	log.Printf("[oauth] ✅ Shop installed successfully: %s (scope: %s)", shop, scope)

	// ── Redirect to Dashboard ─────────────────────────────────────────────────
	// Installation is complete. Send the merchant to the NexusOS dashboard.
	dashboardURL := os.Getenv("SHOPIFY_APP_URL") + "/dashboard?shop=" + url.QueryEscape(shop)
	c.Redirect(http.StatusFound, dashboardURL)
}

// exchangeCodeForToken calls Shopify's token endpoint to swap a temporary auth code
// for a permanent access token.
//
// This is an HTTP POST to: https://{shop}/admin/oauth/access_token
// with our client_id, client_secret, and the code.
// Shopify responds with the access_token and the granted scopes.
func exchangeCodeForToken(shop, code string) (accessToken, scope string, err error) {
	client := &http.Client{Timeout: 10 * time.Second}

	// Build the POST form parameters.
	params := url.Values{}
	params.Set("client_id", os.Getenv("SHOPIFY_CLIENT_ID"))
	params.Set("client_secret", os.Getenv("SHOPIFY_CLIENT_SECRET"))
	params.Set("code", code)

	resp, err := client.PostForm(
		fmt.Sprintf("https://%s/admin/oauth/access_token", shop),
		params,
	)
	if err != nil {
		return "", "", fmt.Errorf("HTTP request to Shopify token endpoint failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", "", fmt.Errorf("Shopify token endpoint returned status %d", resp.StatusCode)
	}

	// Parse the JSON response.
	var result struct {
		AccessToken string `json:"access_token"` // e.g. "shpat_abc123..."
		Scope       string `json:"scope"`        // e.g. "read_orders,write_orders,..."
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", "", fmt.Errorf("failed to decode Shopify token response: %w", err)
	}

	if result.AccessToken == "" {
		return "", "", fmt.Errorf("Shopify returned empty access token")
	}

	return result.AccessToken, result.Scope, nil
}

// generateState creates a cryptographically random hex string used as a CSRF token.
// We use 16 random bytes = 32 hex characters — enough entropy that it's
// computationally infeasible for an attacker to guess.
func generateState() (string, error) {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		return "", fmt.Errorf("failed to generate random state: %w", err)
	}
	return hex.EncodeToString(b), nil // returns e.g. "a3f2b9c14d8e70f1..."
}
