#!/usr/bin/env python3
"""Sync PokemonTool inventory rows into Odoo products.

This is intentionally one-way for now:
PokemonTool inventory/market data -> Odoo product.template sellable products.

Required environment variables:
  POKEMON_POSTGRES_DSN  PostgreSQL DSN for PokemonTool
  ODOO_URL              Example: http://127.0.0.1:8069
  ODOO_DB               Example: pokecard_store
  ODOO_USERNAME         Odoo login email
  ODOO_PASSWORD         Odoo password or API key

Example dry run:
  POKEMON_POSTGRES_DSN='postgresql://pokemontool_user:pokemontool_pass@127.0.0.1:5432/pokemontool' \
  ODOO_URL='http://127.0.0.1:8069' ODOO_DB='pokecard_store' \
  ODOO_USERNAME='admin' ODOO_PASSWORD='admin' \
  python3 odoo/custom_addons/pokecard_storefront/scripts/sync_pokemon_inventory_to_odoo.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xmlrpc.client
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class PokemonInventoryRow:
    id: str
    card_name: str
    set_name: str | None
    card_number: str | None
    external_card_id: str | None
    rarity: str | None
    image_url: str | None
    market_updated_at: str | None
    price_source: str | None
    condition: str | None
    quantity: int
    purchase_price: float | None
    current_value: float | None
    notes: str | None
    asset_type: str | None
    grader: str | None
    grade: str | None
    slab_tier: str | None
    cert_number: str | None
    target_sale_price: float | None
    store_listing_status: str | None
    store_price: float | None
    store_listing_notes: str | None


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def import_postgres_driver() -> tuple[str, Any]:
    try:
        import psycopg

        return "psycopg", psycopg
    except ImportError:
        try:
            import psycopg2
            import psycopg2.extras

            return "psycopg2", (psycopg2, psycopg2.extras)
        except ImportError as exc:
            raise SystemExit(
                "Install psycopg or psycopg2 in the Python environment running this script."
            ) from exc


def fetch_inventory(
    dsn: str, limit: int, user_id: str | None, include_all_inventory: bool
) -> list[PokemonInventoryRow]:
    driver_name, driver = import_postgres_driver()
    where_parts: list[str] = []
    params: list[Any] = []
    if user_id:
        where_parts.append("user_id = %s")
        params.append(user_id)
    if not include_all_inventory:
        where_parts.append("store_listing_status = 'READY'")
    where = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    params.append(limit)
    query = f"""
        SELECT
            id::text,
            card_name,
            set_name,
            card_number,
            external_card_id,
            rarity,
            image_url,
            market_updated_at,
            price_source,
            condition,
            quantity,
            purchase_price::float,
            current_value::float,
            notes,
            asset_type,
            grader,
            grade,
            slab_tier,
            cert_number,
            target_sale_price::float,
            store_listing_status,
            store_price::float,
            store_listing_notes
        FROM inventory
        {where}
        ORDER BY updated_at DESC, acquired_at DESC
        LIMIT %s
    """

    if driver_name == "psycopg":
        from psycopg.rows import dict_row

        with driver.connect(dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
    else:
        psycopg2, extras = driver
        with psycopg2.connect(dsn) as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

    return [PokemonInventoryRow(**dict(row)) for row in rows]


def product_name(row: PokemonInventoryRow) -> str:
    parts = [row.card_name]
    if row.set_name:
        parts.append(row.set_name)
    if row.card_number:
        parts.append(f"#{row.card_number}")
    if row.condition:
        parts.append(row.condition)
    return " - ".join(parts)


def sale_price(row: PokemonInventoryRow, target_margin_pct: float) -> float:
    market = row.current_value or 0.0
    cost = row.purchase_price or 0.0
    margin_price = cost * (1 + target_margin_pct / 100) if cost else 0.0
    target = row.target_sale_price or 0.0
    store = row.store_price or 0.0
    return round(max(market, margin_price, target, store), 2)


def description(row: PokemonInventoryRow) -> str:
    lines = ["Pokemon card inventory synced from PokemonTool."]
    facts = [
        ("Set", row.set_name),
        ("Card number", row.card_number),
        ("Condition", row.condition),
        ("Rarity", row.rarity),
        ("External card ID", row.external_card_id),
        ("Market source", row.price_source),
        ("Asset type", row.asset_type),
        ("Grader", row.grader),
        ("Grade", row.grade),
        ("Certification", row.cert_number),
    ]
    for label, value in facts:
        if value:
            lines.append(f"{label}: {value}")
    if row.notes:
        lines.append(f"Notes: {row.notes}")
    if row.store_listing_notes:
        lines.append(f"Store listing notes: {row.store_listing_notes}")
    return "\n".join(lines)


def condition_value(condition: str | None) -> str | None:
    if not condition:
        return None
    normalized = condition.upper().replace(" ", "_")
    if normalized in {"NM", "LP", "MP", "HP"}:
        return normalized
    if normalized in {"DAMAGED", "SEALED", "GRADED"}:
        return normalized
    return None


def build_product_values(row: PokemonInventoryRow, target_margin_pct: float) -> dict[str, Any]:
    price = sale_price(row, target_margin_pct)
    values: dict[str, Any] = {
        "name": product_name(row),
        "type": "consu",
        "sale_ok": True,
        "purchase_ok": True,
        "is_published": True,
        "list_price": price,
        "standard_price": row.purchase_price or 0.0,
        "default_code": row.external_card_id or row.id[:12],
        "description_sale": description(row),
        "pokemon_inventory_id": row.id,
        "pokemon_external_card_id": row.external_card_id,
        "pokemon_set_name": row.set_name,
        "pokemon_card_number": row.card_number,
        "pokemon_rarity": row.rarity,
        "pokemon_image_url": row.image_url,
        "pokemon_condition": condition_value(row.condition),
        "pokemon_asset_type": row.asset_type or "RAW",
        "pokemon_grader": row.grader,
        "pokemon_grade": row.grade,
        "pokemon_cert_number": row.cert_number,
        "pokemon_acquisition_cost": row.purchase_price or 0.0,
        "pokemon_market_value": row.current_value or 0.0,
        "pokemon_target_margin_pct": target_margin_pct,
        "pokemon_price_source": row.price_source,
        "pokemon_market_updated_at": row.market_updated_at,
        "pokemon_sync_source": "pokemontool",
        "pokemon_last_synced_at": False,
    }
    return {key: value for key, value in values.items() if value is not None}


def authenticate(url: str, db: str, username: str, password: str) -> tuple[int, Any]:
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    if not uid:
        raise SystemExit("Odoo authentication failed")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    return uid, models


def mark_inventory_synced(dsn: str, inventory_ids: list[str]) -> None:
    if not inventory_ids:
        return
    driver_name, driver = import_postgres_driver()
    query = """
        UPDATE inventory
        SET store_listing_status = 'SYNCED', store_synced_at = NOW(), updated_at = NOW()
        WHERE id = ANY(%s::uuid[])
    """
    if driver_name == "psycopg":
        with driver.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (inventory_ids,))
            conn.commit()
    else:
        psycopg2, _ = driver
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (inventory_ids,))
            conn.commit()


def upsert_products(
    models: Any,
    db: str,
    uid: int,
    password: str,
    rows: Iterable[PokemonInventoryRow],
    target_margin_pct: float,
    dry_run: bool,
) -> tuple[dict[str, int], list[str]]:
    counts = {"created": 0, "updated": 0, "seen": 0}
    synced_inventory_ids: list[str] = []
    for row in rows:
        counts["seen"] += 1
        values = build_product_values(row, target_margin_pct)
        domain = [["pokemon_inventory_id", "=", row.id]]
        existing = [] if dry_run else models.execute_kw(
            db, uid, password, "product.template", "search", [domain], {"limit": 1}
        )

        if dry_run:
            print(json.dumps({"match": domain, "status": row.store_listing_status, "values": values}, indent=2, sort_keys=True))
            continue

        if existing:
            models.execute_kw(db, uid, password, "product.template", "write", [existing, values])
            counts["updated"] += 1
        else:
            models.execute_kw(db, uid, password, "product.template", "create", [values])
            counts["created"] += 1
        synced_inventory_ids.append(row.id)
    return counts, synced_inventory_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync PokemonTool inventory into Odoo products")
    parser.add_argument("--limit", type=int, default=100, help="Maximum rows to sync")
    parser.add_argument("--user-id", help="Only sync inventory for one PokemonTool user UUID")
    parser.add_argument("--target-margin-pct", type=float, default=30.0)
    parser.add_argument(
        "--include-all-inventory",
        action="store_true",
        help="Sync all inventory rows instead of only rows marked READY by Add to Store",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print Odoo values without writing")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dsn = require_env("POKEMON_POSTGRES_DSN")
    rows = fetch_inventory(dsn, args.limit, args.user_id, args.include_all_inventory)
    if args.dry_run:
        counts, _ = upsert_products(None, "", 0, "", rows, args.target_margin_pct, dry_run=True)
        print(json.dumps(counts, sort_keys=True))
        return 0

    url = require_env("ODOO_URL").rstrip("/")
    db = require_env("ODOO_DB")
    username = require_env("ODOO_USERNAME")
    password = require_env("ODOO_PASSWORD")
    uid, models = authenticate(url, db, username, password)
    counts, synced_inventory_ids = upsert_products(models, db, uid, password, rows, args.target_margin_pct, dry_run=False)
    mark_inventory_synced(dsn, synced_inventory_ids)
    print(json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
