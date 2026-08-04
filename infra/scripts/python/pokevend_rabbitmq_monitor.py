#!/usr/bin/env python3
"""
SCRIPT: pokevend_rabbitmq_monitor.py
MODULE: Python — Week 2/3
TIES TO THESE REAL PROJECT FILES:
    services/api-consumer/main.py          — scanner_loop() publishes to RabbitMQ
    services/api-consumer/publisher/rabbitmq_publisher.py — pub side
    server/worker/                         — Go consumer side
    services/analytics-engine/trend_analyzer.py — publishes analytics_results queue
    docker-compose.yml lines 57-73         — pokemontool_rabbitmq container

WHAT IT DOES (when complete):
    Monitors RabbitMQ queues in real time using the RabbitMQ HTTP Management API.
    This tells you:
      - Is api-consumer actually publishing card listings?
      - Is Go's notification_worker consuming them fast enough?
      - Are queues backing up (= consumer is lagging)?
      - How many messages per hour flow through each queue?

THE REAL QUEUES in this project (inferred from code):
    "listings"          — api-consumer publishes eBay/TCGplayer listings here
                          Go's notification_worker consumes from here
    "analytics_results" — analytics-engine publishes TREND_CHANGE events here
                          (trend_analyzer.py line 160: channel.queue_declare("analytics_results"))
    "ebay_webhooks"     — eBay sends real-time sold events here (webhook endpoint)

RabbitMQ Management API (runs on port 15672):
    GET /api/queues           → list all queues with message counts
    GET /api/queues/%2F/{name} → details for one queue (%2F = default vhost)
    GET /api/overview         → broker-level stats
    POST /api/queues/%2F/{name}/get → peek at messages WITHOUT consuming them

HOW TO RUN:
    python3 infra/scripts/python/pokevend_rabbitmq_monitor.py
    python3 infra/scripts/python/pokevend_rabbitmq_monitor.py --watch 5   (refresh every 5s)
    python3 infra/scripts/python/pokevend_rabbitmq_monitor.py --peek listings  (show raw messages)
    python3 infra/scripts/python/pokevend_rabbitmq_monitor.py --drain-check    (detect consumer lag)

WHAT YOU LEARN:
    - urllib.request for authenticated HTTP requests (Basic Auth)
    - JSON parsing of complex nested structures
    - base64 encoding for HTTP Basic Auth headers
    - time.sleep for polling loops
    - Reading message bodies to understand data flowing between services
"""

import urllib.request
import urllib.error
import json
import time
import sys
import argparse
import base64
from datetime import datetime
from typing import Optional

# =============================================================================
# CONNECTION CONFIG
# docker-compose.yml lines 62-63: guest/guest credentials
# Management UI port: 15672 (docker-compose.yml line 68)
# =============================================================================
RABBITMQ_HOST     = "localhost"
RABBITMQ_MGMT_PORT = 15672
RABBITMQ_USER     = "guest"
RABBITMQ_PASS     = "guest"
RABBITMQ_VHOST    = "%2F"   # URL-encoded "/" (default vhost)

BASE_URL = f"http://{RABBITMQ_HOST}:{RABBITMQ_MGMT_PORT}/api"

# Queue depth thresholds
WARN_DEPTH    = 50    # Warn if > 50 messages waiting
CRITICAL_DEPTH = 200  # Critical if > 200 messages (consumer seriously lagging)


# =============================================================================
# HTTP CLIENT
# RabbitMQ Management API uses HTTP Basic Auth
# =============================================================================

def make_auth_header() -> str:
    """
    Create HTTP Basic Auth header value.

    HTTP Basic Auth format: "Basic base64(user:password)"
    base64("guest:guest") = "Z3Vlc3Q6Z3Vlc3Q="

    TODO:
    1. Create string: f"{RABBITMQ_USER}:{RABBITMQ_PASS}"
    2. Encode to bytes: .encode("utf-8")
    3. Base64 encode: base64.b64encode(...)
    4. Decode back to string: .decode("utf-8")
    5. Return: f"Basic {encoded}"

    HINT:
        creds = f"{RABBITMQ_USER}:{RABBITMQ_PASS}"
        encoded = base64.b64encode(creds.encode("utf-8")).decode("utf-8")
        return f"Basic {encoded}"
    """
    # YOUR CODE HERE
    return ""  # placeholder


def api_get(path: str) -> Optional[dict | list]:
    """
    Make an authenticated GET request to the RabbitMQ Management API.
    Returns parsed JSON or None if the request fails.

    TODO:
    1. Build URL: BASE_URL + path
    2. Create request: urllib.request.Request(url)
    3. Add auth header: req.add_header("Authorization", make_auth_header())
    4. Open with timeout: urllib.request.urlopen(req, timeout=5)
    5. Parse JSON: json.load(response)
    6. Handle urllib.error.URLError (connection refused) → return None
    7. Handle urllib.error.HTTPError (auth failed = 401) → print error, return None

    HINT:
        url = BASE_URL + path
        req = urllib.request.Request(url)
        req.add_header("Authorization", make_auth_header())
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.load(resp)
        except urllib.error.URLError as e:
            return None
    """
    # YOUR CODE HERE
    return None  # placeholder


# =============================================================================
# QUEUE DATA STRUCTURES
# =============================================================================

class QueueInfo:
    """Parsed information about a single RabbitMQ queue."""

    def __init__(self, raw: dict):
        """
        Parse a queue from the /api/queues response.

        TODO: Extract these fields from the raw dict:
            self.name       = raw["name"]
            self.messages   = raw.get("messages", 0)          — total in queue
            self.ready      = raw.get("messages_ready", 0)    — ready to consume
            self.unacked    = raw.get("messages_unacknowledged", 0)  — being processed
            self.consumers  = raw.get("consumers", 0)         — how many consumers
            self.state      = raw.get("state", "unknown")     — running/idle/crashed
            self.publish_rate = raw.get("message_stats", {}).get("publish_details", {}).get("rate", 0.0)
            self.deliver_rate = raw.get("message_stats", {}).get("deliver_get_details", {}).get("rate", 0.0)
        """
        # YOUR CODE HERE
        self.name         = raw.get("name", "unknown")
        self.messages     = 0      # placeholder
        self.ready        = 0      # placeholder
        self.unacked      = 0      # placeholder
        self.consumers    = 0      # placeholder
        self.state        = "unknown"  # placeholder
        self.publish_rate = 0.0    # placeholder
        self.deliver_rate = 0.0    # placeholder

    @property
    def is_backing_up(self) -> bool:
        """Queue is backing up if depth > threshold and has consumers."""
        return self.messages > WARN_DEPTH and self.consumers > 0

    @property
    def is_orphaned(self) -> bool:
        """Queue has messages but no consumers = messages will never be processed."""
        return self.messages > 0 and self.consumers == 0

    @property
    def lag_description(self) -> str:
        """Human-readable description of queue state."""
        if self.is_orphaned:
            return f"⚠ ORPHANED ({self.messages} msgs, no consumers)"
        elif self.messages > CRITICAL_DEPTH:
            return f"🔴 CRITICAL ({self.messages} msgs backing up)"
        elif self.messages > WARN_DEPTH:
            return f"🟡 WARN ({self.messages} msgs)"
        elif self.messages == 0:
            return "✓ empty"
        else:
            return f"✓ {self.messages} msgs"


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def get_all_queues() -> list[QueueInfo]:
    """
    Fetch all queues from the RabbitMQ API.

    TODO:
    1. Call api_get("/queues") to get list of all queues
    2. Parse each into a QueueInfo object
    3. Return sorted by name for consistent output

    HINT:
        raw_queues = api_get("/queues")
        if not raw_queues:
            return []
        return sorted([QueueInfo(q) for q in raw_queues], key=lambda q: q.name)
    """
    # YOUR CODE HERE
    return []  # placeholder


def get_broker_overview() -> Optional[dict]:
    """
    Get overall RabbitMQ broker stats.
    This shows: total messages, connections, channels, uptime.

    TODO: Call api_get("/overview") and return the result.
    The response includes:
        result["rabbitmq_version"]   — RabbitMQ version
        result["erlang_version"]     — Erlang version (RabbitMQ runs on Erlang)
        result["object_totals"]["connections"] — active connections
        result["message_stats"]["publish_details"]["rate"] — overall publish rate
    """
    # YOUR CODE HERE
    return None  # placeholder


def print_status_table(queues: list[QueueInfo]) -> None:
    """
    Print a table showing all queue states.

    TODO: Print in this format:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    QUEUE                 DEPTH  READY  UNACKED  CONSUMERS  RATE/s
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    listings                  3      3        0          1   2.1/s
    analytics_results         0      0        0          0   0.0/s
    ebay_webhooks             0      0        0          1   0.0/s

    Use:
    print(f"{'QUEUE':<25} {'DEPTH':>6} {'READY':>6} {'UNACKED':>8} {'CONSUMERS':>10} {'RATE':>8}")
    for q in queues:
        print(f"{q.name:<25} {q.messages:>6} {q.ready:>6} {q.unacked:>8} {q.consumers:>10} {q.publish_rate:>6.1f}/s")
        if q.is_orphaned:
            print(f"  ⚠ ORPHANED — messages will never be consumed!")
            print(f"    Is pokemontool_server running? Check: docker logs pokemontool_server")
    """
    # YOUR CODE HERE
    pass


def print_broker_overview(overview: dict) -> None:
    """
    Print broker-level stats.

    TODO: Print:
      RabbitMQ version: 3.x.x
      Active connections: N
      Channels: N
      Total messages: N
      Publish rate: N.N/s
    """
    # YOUR CODE HERE
    pass


def peek_queue(queue_name: str, count: int = 5) -> None:
    """
    Peek at messages in a queue WITHOUT consuming them.
    This lets you see what api-consumer is actually publishing.

    The RabbitMQ HTTP API has a POST endpoint that gets messages
    without removing them from the queue (using ackmode=ack_requeue_true).

    TODO:
    1. Build the payload:
       payload = {
           "count": count,                    — how many messages to peek
           "ackmode": "ack_requeue_true",     — get but put back (non-destructive!)
           "encoding": "auto",               — auto-detect encoding
           "truncate": 50000                  — max message body size
       }
    2. POST to: /queues/%2F/{queue_name}/get
       Use urllib.request.Request with method="POST"
       Add Content-Type: application/json header
       Send data: json.dumps(payload).encode("utf-8")
    3. Parse response — each message has:
       msg["payload"]           → the actual message body (JSON string)
       msg["properties"]        → delivery mode, content type
       msg["payload_bytes"]     → size in bytes
    4. Print each message body parsed as JSON

    WHY: This lets you see EXACTLY what api-consumer is publishing.
    You can verify the message format matches what Go's worker expects.

    HINT — posting authenticated data:
        payload = {...}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/queues/{RABBITMQ_VHOST}/{queue_name}/get",
            data=data,
            method="POST"
        )
        req.add_header("Authorization", make_auth_header())
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            messages = json.load(resp)
    """
    print(f"\nPeeking at queue: {queue_name} (last {count} messages)")
    print("━" * 60)
    # YOUR CODE HERE
    print("(Not implemented — complete the peek_queue TODO above)")


def detect_consumer_lag() -> None:
    """
    Detect if the Go notification_worker is falling behind consuming listings.

    HOW CONSUMER LAG WORKS:
    - api-consumer publishes at rate R (msg/s)
    - Go worker consumes at rate C (msg/s)
    - Depth D = accumulated messages
    - If R > C: queue grows → consumer is falling behind
    - Lag time = D / (R - C) seconds until queue reaches critical

    TODO:
    1. Get all queues
    2. For each queue with consumers:
       - If depth > 0 AND publish_rate > deliver_rate:
         lag_seconds = depth / (publish_rate - deliver_rate)
         print warning with estimated time to fill
    3. For the "listings" queue specifically:
       - This is where eBay/TCGplayer data flows
       - If depth > 100: the Go worker may be down or slow
       - Print: "Start Go worker: docker-compose up -d server"
    """
    print("\nConsumer Lag Analysis:")
    print("━" * 40)
    # YOUR CODE HERE
    print("(Not implemented — complete detect_consumer_lag TODO above)")


# =============================================================================
# MAIN
# =============================================================================

def parse_args() -> argparse.Namespace:
    """
    TODO: Create argument parser with:
      --watch INT    (refresh interval in seconds for live monitor, 0=once)
      --peek NAME    (queue name to peek at messages)
      --drain-check  (flag: run consumer lag detection)
    """
    # YOUR CODE HERE
    class FakeArgs:
        watch      = 0     # 0 = run once
        peek       = None
        drain_check = False
    return FakeArgs()


def main() -> None:
    args = parse_args()

    print("Pokevend RabbitMQ Monitor")
    print(f"Management API: http://{RABBITMQ_HOST}:{RABBITMQ_MGMT_PORT}")
    print(f"Credentials: {RABBITMQ_USER}/{'*' * len(RABBITMQ_PASS)}")
    print("")

    # Test connection first
    overview = get_broker_overview()
    if overview is None:
        print("ERROR: Cannot reach RabbitMQ Management API")
        print(f"  Is pokemontool_rabbitmq running? Check: docker ps")
        print(f"  Web UI should be at: http://{RABBITMQ_HOST}:{RABBITMQ_MGMT_PORT}")
        sys.exit(1)

    if args.peek:
        peek_queue(args.peek)
        return

    if args.drain_check:
        detect_consumer_lag()
        return

    # Main monitoring loop
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Queue Status")
            print("═" * 65)

            print_broker_overview(overview)

            queues = get_all_queues()
            if not queues:
                print("No queues found — have services published anything yet?")
                print("Start api-consumer and wait for a scan cycle to complete")
            else:
                print_status_table(queues)

            if args.watch == 0:
                break

            print(f"\nRefreshing in {args.watch}s (Ctrl+C to stop)...")
            time.sleep(args.watch)
            overview = get_broker_overview()  # refresh

    except KeyboardInterrupt:
        print("\nMonitor stopped.")


if __name__ == "__main__":
    main()
