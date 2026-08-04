#!/usr/bin/env python
"""Pokemon card market data CLI using free APIs."""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / ".cache"
WATCHLIST = ROOT / "watchlist.json"
POKEMONTCG = "https://api.pokemontcg.io/v2"
TCGDEX = "https://api.tcgdex.net/v2/en"
POKETRACE = "https://api.poketrace.com/v1"


def load_env() -> dict[str, str]:
    env = dict(os.environ)
    path = ROOT / ".env"
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return env


def cache_key(url: str) -> Path:
    safe = "".join(c if c.isalnum() else "_" for c in url)[-180:]
    return CACHE_DIR / f"{safe}.json"


def fetch_json(url: str, *, headers: dict[str, str] | None = None, ttl: int = 3600) -> Any:
    CACHE_DIR.mkdir(exist_ok=True)
    path = cache_key(url + json.dumps(headers or {}, sort_keys=True))
    if path.exists() and time.time() - path.stat().st_mtime < ttl:
        return json.loads(path.read_text(encoding="utf-8"))

    default_headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 PokeAi/1.0 (+https://github.com/pokeai)",
    }
    req = Request(url, headers={**default_headers, **(headers or {})})
    try:
        with urlopen(req, timeout=45) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise SystemExit(f"Network error: {exc}") from exc

    data = json.loads(body)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return data


def money(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"${value:,.2f}"
    return "-"


def get_nested(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def best_tcg_market(card: dict[str, Any]) -> tuple[str, float | None]:
    prices = get_nested(card, "tcgplayer.prices") or {}
    best_name = "-"
    best_value = None
    for variant, fields in prices.items():
        value = fields.get("market") or fields.get("mid") or fields.get("low")
        if isinstance(value, (int, float)) and (best_value is None or value > best_value):
            best_name = variant
            best_value = float(value)
    return best_name, best_value


def print_rows(rows: list[list[Any]], headers: list[str]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))


def pokemon_search(query: str, limit: int) -> list[dict[str, Any]]:
    params = {
        "q": f'name:"{query}"',
        "pageSize": limit,
        "orderBy": "name",
    }
    data = fetch_json(f"{POKEMONTCG}/cards?{urlencode(params)}", ttl=1800)
    cards = data.get("data", [])
    if cards:
        return cards

    # Fallback for lowercase, partial, or slightly misspelled searches.
    # PokemonTCG does not provide true fuzzy search, so fetch a broader candidate
    # set using stable token prefixes, then rank locally by close name matches.
    tokens = [token.strip() for token in query.replace("-", " ").split() if len(token.strip()) >= 3]
    if not tokens:
        return []
    broad_terms = " ".join(f'name:*{quote_token(token[:4])}*' for token in tokens[:2])
    params = {
        "q": broad_terms,
        "pageSize": max(limit * 4, 20),
        "orderBy": "name",
    }
    data = fetch_json(f"{POKEMONTCG}/cards?{urlencode(params)}", ttl=1800)
    candidates = data.get("data", [])
    return sorted(candidates, key=lambda card: search_score(query, card), reverse=True)[:limit]


def quote_token(token: str) -> str:
    return "".join(ch for ch in token if ch.isalnum())


def search_score(query: str, card: dict[str, Any]) -> float:
    name = str(card.get("name") or "")
    set_name = str(get_nested(card, "set.name") or "")
    haystack = f"{name} {set_name}".lower()
    needle = query.lower()
    ratio = difflib.SequenceMatcher(None, needle, haystack).ratio()
    token_bonus = sum(0.2 for token in needle.split() if token[:4] and token[:4] in haystack)
    price_bonus = 0.1 if best_tcg_market(card)[1] is not None else 0.0
    return ratio + token_bonus + price_bonus


def pokemon_card(card_id: str) -> dict[str, Any]:
    data = fetch_json(f"{POKEMONTCG}/cards/{quote(card_id)}", ttl=1800)
    return data["data"]


def cmd_search(args: argparse.Namespace) -> None:
    cards = pokemon_search(args.query, args.limit)
    rows = []
    for card in cards:
        variant, value = best_tcg_market(card)
        rows.append(
            [
                card.get("id", ""),
                card.get("name", ""),
                get_nested(card, "set.name") or "",
                card.get("number", ""),
                card.get("rarity", "-"),
                variant,
                money(value),
                get_nested(card, "tcgplayer.updatedAt") or "-",
            ]
        )
    print_rows(rows, ["id", "name", "set", "#", "rarity", "best variant", "market", "updated"])


def card_summary(card: dict[str, Any]) -> None:
    print(f"{card.get('name')} [{card.get('id')}]")
    print(f"Set: {get_nested(card, 'set.name')} ({get_nested(card, 'set.series')}) #{card.get('number')}")
    print(f"Rarity: {card.get('rarity', '-')}")
    print(f"Image: {get_nested(card, 'images.large') or get_nested(card, 'images.small') or '-'}")

    prices = get_nested(card, "tcgplayer.prices") or {}
    if prices:
        print("\nTCGPlayer")
        rows = []
        for variant, fields in prices.items():
            rows.append(
                [
                    variant,
                    money(fields.get("low")),
                    money(fields.get("mid")),
                    money(fields.get("high")),
                    money(fields.get("market")),
                    money(fields.get("directLow")),
                ]
            )
        print_rows(rows, ["variant", "low", "mid", "high", "market", "direct"])
        print(f"Updated: {get_nested(card, 'tcgplayer.updatedAt')}")
        print(f"URL: {get_nested(card, 'tcgplayer.url')}")
    else:
        print("\nTCGPlayer: no pricing data")

    cm = get_nested(card, "cardmarket.prices") or {}
    if cm:
        print("\nCardmarket")
        rows = [
            ["averageSellPrice", money(cm.get("averageSellPrice"))],
            ["trendPrice", money(cm.get("trendPrice"))],
            ["lowPrice", money(cm.get("lowPrice"))],
            ["avg7", money(cm.get("avg7"))],
            ["avg30", money(cm.get("avg30"))],
        ]
        print_rows(rows, ["metric", "value"])
        print(f"Updated: {get_nested(card, 'cardmarket.updatedAt')}")
        print(f"URL: {get_nested(card, 'cardmarket.url')}")
    else:
        print("\nCardmarket: no pricing data")


def cmd_card(args: argparse.Namespace) -> None:
    card_summary(pokemon_card(args.card_id))


def cmd_compare(args: argparse.Namespace) -> None:
    cards = pokemon_search(args.query, args.limit)
    rows = []
    for card in cards:
        variant, tcg_market = best_tcg_market(card)
        cm_trend = get_nested(card, "cardmarket.prices.trendPrice")
        spread = None
        if isinstance(tcg_market, (int, float)) and isinstance(cm_trend, (int, float)):
            spread = tcg_market - cm_trend
        rows.append(
            [
                card.get("id"),
                card.get("name"),
                get_nested(card, "set.name"),
                variant,
                money(tcg_market),
                money(cm_trend),
                money(spread),
            ]
        )
    print_rows(rows, ["id", "name", "set", "variant", "tcg market", "cardmarket trend", "spread"])


def tcgdex_search(query: str, limit: int) -> list[dict[str, Any]]:
    url = f"{TCGDEX}/cards?{urlencode({'name': query, 'pagination:itemsPerPage': limit})}"
    return fetch_json(url, ttl=86400)


def cmd_tcgdex(args: argparse.Namespace) -> None:
    cards = tcgdex_search(args.query, args.limit)
    rows = [[c.get("id"), c.get("localId", "-"), c.get("name"), c.get("image", "-")] for c in cards]
    print_rows(rows, ["tcgdex id", "local #", "name", "image"])


def read_watchlist() -> list[str]:
    if not WATCHLIST.exists():
        return []
    return json.loads(WATCHLIST.read_text(encoding="utf-8"))


def write_watchlist(ids: list[str]) -> None:
    WATCHLIST.write_text(json.dumps(sorted(set(ids)), indent=2), encoding="utf-8")


def cmd_watch(args: argparse.Namespace) -> None:
    ids = read_watchlist()
    if args.watch_command == "add":
        ids.extend(args.card_ids)
        write_watchlist(ids)
        print(f"watchlist now has {len(set(ids))} card(s)")
        return
    if args.watch_command == "remove":
        remove = set(args.card_ids)
        ids = [i for i in ids if i not in remove]
        write_watchlist(ids)
        print(f"watchlist now has {len(ids)} card(s)")
        return

    rows = []
    for card_id in ids:
        try:
            card = pokemon_card(card_id)
        except SystemExit as exc:
            rows.append([card_id, "ERROR", str(exc), "-", "-", "-"])
            continue
        variant, value = best_tcg_market(card)
        rows.append(
            [
                card_id,
                card.get("name"),
                get_nested(card, "set.name"),
                variant,
                money(value),
                get_nested(card, "tcgplayer.updatedAt") or "-",
            ]
        )
    print_rows(rows, ["id", "name", "set", "variant", "market", "updated"])


def cmd_export(args: argparse.Namespace) -> None:
    ids = read_watchlist()
    with Path(args.output).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "name", "set", "variant", "tcg_market", "tcg_updated", "cardmarket_trend"])
        for card_id in ids:
            card = pokemon_card(card_id)
            variant, value = best_tcg_market(card)
            writer.writerow(
                [
                    card_id,
                    card.get("name"),
                    get_nested(card, "set.name"),
                    variant,
                    value or "",
                    get_nested(card, "tcgplayer.updatedAt") or "",
                    get_nested(card, "cardmarket.prices.trendPrice") or "",
                ]
            )
    print(f"exported {len(ids)} card(s) to {args.output}")


def cmd_poketrace(args: argparse.Namespace) -> None:
    key = load_env().get("POKETRACE_API_KEY")
    if not key:
        raise SystemExit("Set POKETRACE_API_KEY in .env to use PokeTrace.")
    data = fetch_json(f"{POKETRACE}/cards/{quote(args.card_id)}", headers={"X-API-Key": key}, ttl=1800)
    print(json.dumps(data, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Free Pokemon card market data")
    sub = parser.add_subparsers(required=True)

    search = sub.add_parser("search", help="Search cards with TCGPlayer/Cardmarket prices")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)
    search.set_defaults(func=cmd_search)

    card = sub.add_parser("card", help="Show detailed prices for a PokemonTCG card id")
    card.add_argument("card_id")
    card.set_defaults(func=cmd_card)

    compare = sub.add_parser("compare", help="Compare TCGPlayer vs Cardmarket for search results")
    compare.add_argument("query")
    compare.add_argument("--limit", type=int, default=10)
    compare.set_defaults(func=cmd_compare)

    tcgdex = sub.add_parser("tcgdex", help="Search TCGdex metadata")
    tcgdex.add_argument("query")
    tcgdex.add_argument("--limit", type=int, default=10)
    tcgdex.set_defaults(func=cmd_tcgdex)

    watch = sub.add_parser("watch", help="Manage a local card watchlist")
    watch_sub = watch.add_subparsers(dest="watch_command", required=True)
    watch_add = watch_sub.add_parser("add")
    watch_add.add_argument("card_ids", nargs="+")
    watch_add.set_defaults(func=cmd_watch)
    watch_remove = watch_sub.add_parser("remove")
    watch_remove.add_argument("card_ids", nargs="+")
    watch_remove.set_defaults(func=cmd_watch)
    watch_list = watch_sub.add_parser("list")
    watch_list.set_defaults(func=cmd_watch)

    export = sub.add_parser("export", help="Export watchlist pricing to CSV")
    export.add_argument("--output", default="watchlist_prices.csv")
    export.set_defaults(func=cmd_export)

    poketrace = sub.add_parser("poketrace", help="Optional PokeTrace raw/graded pricing by PokeTrace id")
    poketrace.add_argument("card_id")
    poketrace.set_defaults(func=cmd_poketrace)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
