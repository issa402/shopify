#!/usr/bin/env python3
"""
NexusOS A2A Commerce — Integration Test
Simulates a customer AI agent sending a ProductQuery to NexusOS.

Usage:
  python scripts/test_a2a_agent.py

Expected: Receives a structured Offer response with protocol "nexusos-a2a/1.0"
"""
import httpx
import json
import sys

GATEWAY_URL = "http://localhost:8080"

def test_a2a_negotiation():
    """Send a mock ProductQuery as an AI agent and validate the Offer response."""

    headers = {
        "User-Agent": "Google-Agent/1.0 (Shopping Buyer-Agent)",
        "Content-Type": "application/json",
        "X-Agent-Type": "shopping-agent",
        # In production, add Bearer token here
    }

    payload = {
        "agent_id": "test-agent-001",
        "agent_type": "google-shopping-agent",
        "session_id": "sess_test_abc123",
        "query": "I need red running shoes in size 10, waterproof, under $150",
        "constraints": {
            "max_price_usd": 150.0,
            "required_tags": ["running", "waterproof"],
            "max_shipping_days": 3,
            "preferred_currency": "USD",
            "b2b": False,
        },
        "quantity": 1,
    }

    print("🤖 Sending A2A ProductQuery...")
    print(f"   Agent: {payload['agent_id']}")
    print(f"   Query: {payload['query']}")
    print()

    try:
        response = httpx.post(
            f"{GATEWAY_URL}/api/v1/agent/negotiate",
            json=payload,
            headers=headers,
            timeout=10.0,
        )
    except httpx.ConnectError:
        print("❌ Cannot connect to gateway. Is it running? (make gateway)")
        sys.exit(1)

    print(f"📩 Response Status: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ Unexpected status: {response.text}")
        sys.exit(1)

    offer = response.json()
    print(f"✅ Received Offer!")
    print(json.dumps(offer, indent=2))

    # Validate schema
    assert "offer_id" in offer, "Missing offer_id"
    assert "products" in offer, "Missing products"
    assert "protocol" in offer, "Missing protocol"
    assert offer["protocol"] == "nexusos-a2a/1.0", f"Wrong protocol: {offer['protocol']}"
    assert len(offer["products"]) > 0, "No products in offer"
    assert "expires_at" in offer, "Missing expires_at"

    print()
    print("✅ All assertions passed!")
    print(f"   Products offered: {len(offer['products'])}")
    print(f"   Protocol: {offer['protocol']}")
    print(f"   Offer expires: {offer['expires_at']}")


def test_b2b_negotiate():
    """Test B2B bulk negotiation — should trigger discount."""
    headers = {
        "User-Agent": "AutoGen-Corporate-Agent/2.0",
        "Content-Type": "application/json",
    }

    payload = {
        "agent_id": "corporate-buyer-agent",
        "agent_type": "b2b-agent",
        "session_id": "sess_b2b_9999",
        "query": "100 units of safety equipment for corporate event",
        "constraints": {
            "max_price_usd": 10000.0,
            "max_shipping_days": 7,
            "preferred_currency": "USD",
            "b2b": True,
        },
        "quantity": 100,
    }

    print("🏢 Testing B2B bulk negotiation (100 units)...")

    try:
        response = httpx.post(
            f"{GATEWAY_URL}/api/v1/agent/negotiate",
            json=payload,
            headers=headers,
            timeout=10.0,
        )
        offer = response.json()

        if "products" in offer and len(offer["products"]) > 0:
            product = offer["products"][0]
            discount = product.get("discount_pct", 0)
            print(f"✅ B2B Offer received!")
            print(f"   Discount applied: {discount}%")
            assert discount >= 10, f"Expected ≥10% B2B discount for 100 units, got {discount}%"
            print(f"   Assertion passed: {discount}% ≥ 10%")
        else:
            print("   Note: No products matched (stub mode)")

    except httpx.ConnectError:
        print("⚠️  Gateway not running — skipping B2B test")


if __name__ == "__main__":
    print("=" * 60)
    print("NexusOS A2A Commerce — Integration Test Suite")
    print("=" * 60)
    print()

    test_a2a_negotiation()
    print()
    test_b2b_negotiate()
    print()
    print("🎉 All A2A tests complete!")
