// Package webhook contains focused tests for Shopify webhook security behavior.
package webhook

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"testing"
)

func signedBody(body string, secret string) string {
	// Build the same HMAC-SHA256 signature Shopify sends in webhook headers.
	mac := hmac.New(sha256.New, []byte(secret))
	// Feed the raw request body into the HMAC calculator exactly as received.
	mac.Write([]byte(body))
	// Shopify sends the binary HMAC digest as a base64-encoded string.
	return base64.StdEncoding.EncodeToString(mac.Sum(nil))
}

func TestVerifyHMAC(t *testing.T) {
	// Production mode requires a valid Shopify signature.
	t.Setenv("GO_ENV", "production")
	// The test secret mirrors SHOPIFY_WEBHOOK_SECRET without using a real secret.
	t.Setenv("SHOPIFY_WEBHOOK_SECRET", "test_secret_key_12345")

	// The body must be signed byte-for-byte, matching Shopify's webhook contract.
	body := `{"id":12345,"total_price":"99.00"}`
	// A valid signature should pass constant-time verification.
	validSignature := signedBody(body, "test_secret_key_12345")

	tests := []struct {
		name      string
		signature string
		want      bool
	}{
		// Valid signatures protect real webhook ingestion from spoofed requests.
		{name: "valid signature", signature: validSignature, want: true},
		// Invalid signatures must be rejected before parsing or publishing events.
		{name: "invalid signature", signature: "definitely_wrong", want: false},
		// Missing signatures must be rejected in production.
		{name: "empty signature", signature: "", want: false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// verifyHMAC is package-private, so this test lives beside the handler.
			got := verifyHMAC([]byte(body), tt.signature)
			if got != tt.want {
				t.Fatalf("verifyHMAC() = %v, want %v", got, tt.want)
			}
		})
	}
}
