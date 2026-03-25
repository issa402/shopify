// Package pokemon provides a client for calling the PokémonTool microservice.
//
// WHAT IS POKEMONTOOL?
// PokémonTool is a fully-built, separate microservice (Go backend on port 3001)
// that tracks Pokemon TCG card prices across eBay and TCGplayer in real-time.
// It has its own database, analytics engine, and REST API.
//
// WHY DOES NEXUSOS NEED IT?
// Our Shopify store sells Pokemon TCG cards. We need to know real-time market
// prices so that:
//   - When we negotiate with a buyer AI agent (A2A), we use real market prices
//     instead of guessing
//   - When PokémonTool detects a card selling 20%+ below market, our AI agents
//     can decide whether to buy it and resell on our Shopify store
//   - When market trends change (RISING/FALLING), our agents can reprice our
//     Shopify listings automatically
//
// HOW WE CALL IT:
// PokémonTool exposes a standard REST API. We call it with HTTP GET/POST requests.
// We use PokémonTool's EXISTING endpoints — we don't need to build anything new
// in PokémonTool, just consume its API from here.
//
// KEY POKEMONTOOL ENDPOINTS WE USE:
//   GET  /api/cards/search?q={name}    → get price + trend for a specific card
//   GET  /api/cards/trending           → get trending cards for deal opportunities
//   GET  /api/deals                    → today's cards listed below market price
//   GET  /api/inventory                → what cards we currently own
package pokemon

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"time"
)

// Client is the HTTP client for talking to the PokémonTool API.
// It's a thin wrapper — it just handles the HTTP calls and parses responses.
// All the business logic (should we buy this card? should we reprice?) lives
// in the Python AI service agents, not here.
type Client struct {
	baseURL    string       // e.g. "http://pokemon-server:3001"
	httpClient *http.Client // shared HTTP client with timeout
	apiSecret  string       // shared secret for internal auth (X-Internal-Secret header)
}

// NewClient creates a PokémonTool API client.
// Called once at startup in main.go and injected into wherever it's needed.
func NewClient() *Client {
	baseURL := os.Getenv("POKEMONTOOL_API_URL")
	if baseURL == "" {
		// Default for local dev — PokémonTool running on localhost
		baseURL = "http://localhost:3001"
		log.Println("[pokemon] POKEMONTOOL_API_URL not set, defaulting to http://localhost:3001")
	}

	return &Client{
		baseURL:   baseURL,
		apiSecret: os.Getenv("POKEMONTOOL_API_SECRET"),
		httpClient: &http.Client{
			// 5-second timeout: if PokémonTool is slow, we fail fast instead
			// of blocking an A2A negotiation response for the buyer agent
			Timeout: 5 * time.Second,
		},
	}
}

// CardPrice holds the pricing and trend data for a single Pokemon TCG card.
// This maps to PokémonTool's card response shape.
type CardPrice struct {
	CardID         string  `json:"card_id"`          // e.g. "base1-4"
	Name           string  `json:"name"`             // e.g. "Charizard"
	SetName        string  `json:"set_name"`         // e.g. "Base Set"
	PriceTCGPlayer float64 `json:"price_tcgplayer"`  // TCGplayer market price (USD)
	PriceEbay      float64 `json:"price_ebay"`       // Average recent eBay sold price (USD)
	TrendLabel     string  `json:"trend_label"`      // "RISING", "STABLE", or "FALLING"
	TrendingScore  int     `json:"trending_score"`   // -100 to 100 (negative = falling)
}

// Deal represents a card that PokémonTool has identified as selling below market price.
// These are computed by PokémonTool's analytics engine every hour.
type Deal struct {
	CardName    string  `json:"card_name"`    // e.g. "Charizard Base Set"
	MarketPrice float64 `json:"market_price"` // TCGplayer "true" market price
	BestPrice   float64 `json:"best_price"`   // cheapest current eBay listing
	SavingsPct  float64 `json:"savings_pct"`  // e.g. 28.5 means 28.5% below market
	EbayURL     string  `json:"ebay_url"`     // direct link to the eBay listing
	DealDate    string  `json:"deal_date"`    // "2026-03-21" — reset daily
}

// GetCardPrice fetches the current market price and trend for a specific card.
//
// WHEN THIS IS CALLED:
// During A2A negotiation — when a buyer agent asks for a Charizard,
// we call this to find out what the real market price is so we can
// make a fair offer instead of using hardcoded stub prices.
//
// Example:
//
//	price, err := client.GetCardPrice(ctx, "Charizard Base Set")
//	// price.PriceTCGPlayer = 4200.00
//	// price.TrendLabel = "RISING"
//	// → We know the market is going up, so we reduce our discount offer
func (c *Client) GetCardPrice(ctx context.Context, cardName string) (*CardPrice, error) {
	// Build the URL with the search query properly URL-encoded.
	// "Charizard Base Set" → "Charizard+Base+Set" in the URL
	endpoint := fmt.Sprintf("%s/api/cards/search?q=%s", c.baseURL, url.QueryEscape(cardName))

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to build request: %w", err)
	}

	// Add the internal secret header so PokémonTool knows this is us, not a random caller.
	req.Header.Set("X-Internal-Secret", c.apiSecret)
	req.Header.Set("Accept", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		// PokémonTool might be down. We return an error but the caller
		// (negotiation engine) should fall back to a default price rather than crash.
		return nil, fmt.Errorf("pokemontool /api/cards/search request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		// Card doesn't exist in PokémonTool's database yet.
		return nil, fmt.Errorf("card %q not found in PokémonTool", cardName)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("pokemontool returned status %d for card search", resp.StatusCode)
	}

	// PokémonTool returns an array of cards (search might return multiple matches).
	// We take the first result.
	var cards []CardPrice
	if err := json.NewDecoder(resp.Body).Decode(&cards); err != nil {
		return nil, fmt.Errorf("failed to decode card search response: %w", err)
	}

	if len(cards) == 0 {
		return nil, fmt.Errorf("no cards matched %q in PokémonTool", cardName)
	}

	log.Printf("[pokemon] GetCardPrice %q → TCGPlayer=$%.2f eBay=$%.2f trend=%s",
		cardName, cards[0].PriceTCGPlayer, cards[0].PriceEbay, cards[0].TrendLabel)

	return &cards[0], nil
}

// GetDeals fetches today's deal cards from PokémonTool.
// These are cards where the current best eBay price is >20% below TCGplayer market.
//
// WHEN THIS IS CALLED:
// Our Kafka consumer receives "pokemon.deals" events. For each deal,
// it calls this to get full details, then decides whether to create a
// draft Purchase Order for the merchant to approve.
//
// IMPORTANT: PokémonTool already computed these deals — we're just fetching
// pre-computed results. No heavy processing needed here.
func (c *Client) GetDeals(ctx context.Context) ([]Deal, error) {
	endpoint := fmt.Sprintf("%s/api/deals", c.baseURL)

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to build deals request: %w", err)
	}

	req.Header.Set("X-Internal-Secret", c.apiSecret)
	req.Header.Set("Accept", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("pokemontool /api/deals request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("pokemontool /api/deals returned status %d", resp.StatusCode)
	}

	var deals []Deal
	if err := json.NewDecoder(resp.Body).Decode(&deals); err != nil {
		return nil, fmt.Errorf("failed to decode deals response: %w", err)
	}

	log.Printf("[pokemon] GetDeals → %d active deals today", len(deals))
	return deals, nil
}

// GetTrendingCards fetches cards whose prices are significantly moving up or down.
// PokémonTool's analytics engine runs linear regression on 7-day price history
// and scores each card from -100 (falling fast) to +100 (rising fast).
//
// WHEN THIS IS CALLED:
// Our LogisticsAgent uses trending data to decide:
//   - If a card we own is RISING: hold it, don't discount on Shopify
//   - If a card is FALLING: consider running a flash sale to move inventory
func (c *Client) GetTrendingCards(ctx context.Context, limit int) ([]CardPrice, error) {
	endpoint := fmt.Sprintf("%s/api/cards/trending?limit=%d", c.baseURL, limit)

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to build trending request: %w", err)
	}

	req.Header.Set("X-Internal-Secret", c.apiSecret)
	req.Header.Set("Accept", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("pokemontool /api/cards/trending request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("pokemontool /api/cards/trending returned status %d", resp.StatusCode)
	}

	var cards []CardPrice
	if err := json.NewDecoder(resp.Body).Decode(&cards); err != nil {
		return nil, fmt.Errorf("failed to decode trending cards response: %w", err)
	}

	log.Printf("[pokemon] GetTrendingCards → %d trending cards", len(cards))
	return cards, nil
}

// IsAvailable checks if PokémonTool is reachable.
// Used at startup and in our /health endpoint to report integration status.
func (c *Client) IsAvailable(ctx context.Context) bool {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+"/health", nil)
	if err != nil {
		return false
	}
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return false
	}
	resp.Body.Close()
	return resp.StatusCode == http.StatusOK
}
