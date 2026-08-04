#!/usr/bin/env python
"""Small LAN API for PokeAi card pricing."""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

import pokeai


def nested(data: dict[str, Any], path: str) -> Any:
    return pokeai.get_nested(data, path)


def price_summary(card: dict[str, Any]) -> dict[str, Any]:
    variant, market = pokeai.best_tcg_market(card)
    return {
        "id": card.get("id"),
        "name": card.get("name"),
        "set": nested(card, "set.name"),
        "series": nested(card, "set.series"),
        "number": card.get("number"),
        "rarity": card.get("rarity"),
        "image": nested(card, "images.large") or nested(card, "images.small"),
        "bestVariant": variant,
        "market": market,
        "tcgplayerUpdatedAt": nested(card, "tcgplayer.updatedAt"),
        "tcgplayerUrl": nested(card, "tcgplayer.url"),
        "cardmarketTrend": nested(card, "cardmarket.prices.trendPrice"),
        "cardmarketUpdatedAt": nested(card, "cardmarket.updatedAt"),
        "cardmarketUrl": nested(card, "cardmarket.url"),
    }


class PokeAiHandler(BaseHTTPRequestHandler):
    server_version = "PokeAiAPI/1.0"

    def do_GET(self) -> None:
        if not self.client_allowed():
            self.write_json({"error": "forbidden"}, HTTPStatus.FORBIDDEN)
            return

        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        try:
            if parsed.path == "/health":
                self.write_json({"ok": True})
            elif parsed.path == "/search":
                self.handle_search(params)
            elif parsed.path.startswith("/card/"):
                card_id = parsed.path.removeprefix("/card/").strip("/")
                self.handle_card(card_id)
            elif parsed.path == "/watchlist":
                self.handle_watchlist()
            else:
                self.write_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except SystemExit as exc:
            self.write_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
        except Exception as exc:
            self.write_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_search(self, params: dict[str, list[str]]) -> None:
        query = first(params, "q")
        if not query:
            self.write_json({"error": "missing q query parameter"}, HTTPStatus.BAD_REQUEST)
            return

        limit = parse_limit(first(params, "limit"), default=10)
        cards = pokeai.pokemon_search(query, limit)
        self.write_json({"query": query, "count": len(cards), "cards": [price_summary(card) for card in cards]})

    def handle_card(self, card_id: str) -> None:
        if not card_id:
            self.write_json({"error": "missing card id"}, HTTPStatus.BAD_REQUEST)
            return
        self.write_json({"card": price_summary(pokeai.pokemon_card(card_id))})

    def handle_watchlist(self) -> None:
        cards = []
        for card_id in pokeai.read_watchlist():
            cards.append(price_summary(pokeai.pokemon_card(card_id)))
        self.write_json({"count": len(cards), "cards": cards})

    def client_allowed(self) -> bool:
        allowed_ips = self.server.allowed_ips  # type: ignore[attr-defined]
        if not allowed_ips:
            return True
        client_ip = self.client_address[0]
        return client_ip in allowed_ips

    def write_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        client_ip = self.client_address[0]
        print(f"{client_ip} - {format % args}")


def first(params: dict[str, list[str]], key: str) -> str | None:
    values = params.get(key)
    if not values:
        return None
    return values[0]


def parse_limit(raw: str | None, *, default: int) -> int:
    if raw is None:
        return default
    try:
        limit = int(raw)
    except ValueError:
        return default
    return max(1, min(limit, 100))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the PokeAi LAN JSON API")
    parser.add_argument("--host", default="127.0.0.1", help="Host/IP to bind. Use 0.0.0.0 for LAN access.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--allow-ip",
        action="append",
        default=[],
        help="Client IP allowed to call the API. Can be repeated. Empty means allow all.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    server = ThreadingHTTPServer((args.host, args.port), PokeAiHandler)
    server.allowed_ips = set(args.allow_ip)
    allow_text = ", ".join(sorted(server.allowed_ips)) if server.allowed_ips else "all clients"
    print(f"PokeAi API listening on http://{args.host}:{args.port}")
    print(f"Allowed clients: {allow_text}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping PokeAi API")


if __name__ == "__main__":
    main()
