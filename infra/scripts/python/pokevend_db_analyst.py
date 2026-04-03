#!/usr/bin/env python3
"""
SCRIPT: pokevend_db_analyst.py
MODULE: Python + Linux — Week 2
TIES TO THESE REAL PROJECT FILES:
    store/card_store.go      — SQL queries this script mirrors in Python
    models/card.go           — the Card struct (same fields we query)
    config/config.go         — DB connection details

WHAT IT DOES (when complete):
    Connects to the nexusos-postgres container and runs analytics on your
    REAL card data. This is the exact analysis a data engineer or backend
    engineer would produce to understand the state of the product.

    You are NOT using a Python PostgreSQL library (psycopg2).
    You are running queries through "docker exec ... psql" and parsing
    the output in Python. This teaches you BOTH tools simultaneously.

THE REAL DATABASE SCHEMA (from your migrations or card_store.go queries):
    Table: cards
      card_id        TEXT PRIMARY KEY
      name           TEXT
      set_name       TEXT
      set_code       TEXT
      image_url      TEXT
      trending_score FLOAT
      trend_label    TEXT  ('RISING', 'FALLING', 'STABLE')
      pct_change_7d  FLOAT
      price_ebay     FLOAT
      price_tcgplayer FLOAT
      price_facebook  FLOAT
      price_mercari   FLOAT
      last_updated   TIMESTAMP

    Table: price_history
      card_id    TEXT
      date       DATE
      avg_price  FLOAT
      price_ebay FLOAT
      price_tcgplayer FLOAT

HOW TO RUN:
    python3 infra/scripts/python/pokevend_db_analyst.py
    python3 infra/scripts/python/pokevend_db_analyst.py --report trending
    python3 infra/scripts/python/pokevend_db_analyst.py --report prices
    python3 infra/scripts/python/pokevend_db_analyst.py --report search --query charizard
    python3 infra/scripts/python/pokevend_db_analyst.py --export /tmp/cards.json

WHAT YOU LEARN:
    - Running subprocess commands and parsing tabular output
    - String parsing and float conversion
    - Statistical analysis (min, max, mean, percentiles)
    - JSON export of analyzed data
    - Error handling for DB operations specifically
"""

import subprocess
import json
import sys
import os
import argparse
import statistics
from pathlib import Path
from datetime import datetime
from typing import Optional

# =============================================================================
# DB CONNECTION CONFIG
# These match config/config.go EXACTLY.
# In production these would come from env vars.
# =============================================================================
DB_CONTAINER = "nexusos-postgres"
DB_NAME      = os.getenv("POSTGRES_DB",       "pokemontool")
DB_USER      = os.getenv("POSTGRES_USER",     "pokemontool_user")
# We do NOT use the password here because docker exec runs as the postgres
# superuser inside the container — no password needed for local connections.


# =============================================================================
# DATABASE QUERY RUNNER
# This is the core pattern: run psql inside the container, parse output.
# =============================================================================

class PokevengDB:
    """
    Wrapper around docker exec psql for running queries against nexusos-postgres.

    This teaches you the same patterns you'd use with psycopg2 or any ORM,
    but using only subprocess — zero external Python dependencies needed.
    """

    def __init__(self, container: str = DB_CONTAINER,
                 dbname: str = DB_NAME, user: str = DB_USER):
        self.container = container
        self.dbname    = dbname
        self.user      = user

    def execute(self, sql: str, expect_rows: bool = True) -> list[list[str]]:
        """
        Run a SQL query and return results as a list of rows.
        Each row is a list of strings (column values).

        psql flags used:
          -t      = tuples only (no column headers, no row count footer)
          -A      = unaligned output (use | as separator, not spaces)
          -F'|'   = field separator is | (safe for card names with commas)
          -c SQL  = the query to run

        TODO:
        1. Build the psql command as a list:
           ["docker", "exec", self.container,
            "psql", "-U", self.user, "-d", self.dbname,
            "-t", "-A", "-F|", "-c", sql]

        2. Run with subprocess.run(cmd, capture_output=True, text=True, check=False)

        3. If returncode != 0:
           - Check if it's "does not exist" (table missing = migrations not run)
           - Check if it's connection failure (postgres is down)
           - Raise RuntimeError with helpful message

        4. Parse stdout: split by newline, then each line by "|"
           Skip empty lines.
           Return as list of lists.

        HINT:
            cmd = ["docker", "exec", self.container,
                   "psql", "-U", self.user, "-d", self.dbname,
                   "-t", "-A", "-F|", "-c", sql]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                raise RuntimeError(f"Query failed: {result.stderr.strip()}")
            rows = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    rows.append(line.split('|'))
            return rows
        """
        # YOUR CODE HERE
        raise NotImplementedError("Implement execute() — see docstring above")

    def query_one(self, sql: str) -> Optional[str]:
        """
        Run a query that returns a single value (like COUNT or MAX).
        Returns the value as a string, or None if no result.

        TODO: Call self.execute(sql), return rows[0][0] if rows else None
        """
        # YOUR CODE HERE
        return None  # placeholder

    def query_cards(self, sql: str) -> list[dict]:
        """
        Run a SELECT on the cards table and return list of dicts.
        Each dict has keys matching the cards table columns.

        TODO:
        1. Call self.execute(sql)
        2. For each row, create a dict mapping column names to values
           Column order: card_id, name, set_name, set_code, image_url,
                         trending_score, trend_label, pct_change_7d,
                         price_ebay, price_tcgplayer, price_facebook,
                         price_mercari, last_updated
        3. Convert numeric columns to float (use float(val) with try/except)
        4. Return list of dicts
        """
        # These are the exact columns from card_store.go SELECT statements
        # card_store.go lines 89-91: SELECT card_id,name,set_name,...
        CARD_COLUMNS = [
            "card_id", "name", "set_name", "set_code", "image_url",
            "trending_score", "trend_label", "pct_change_7d",
            "price_ebay", "price_tcgplayer", "price_facebook",
            "price_mercari", "last_updated"
        ]
        NUMERIC_COLUMNS = {
            "trending_score", "pct_change_7d",
            "price_ebay", "price_tcgplayer", "price_facebook", "price_mercari"
        }

        # YOUR CODE HERE
        return []  # placeholder


# =============================================================================
# ANALYTICS FUNCTIONS
# Each one mirrors a real business question about the Pokevend platform.
# =============================================================================

def report_card_summary(db: PokevengDB) -> None:
    """
    Print a high-level summary of the card database.

    TODO:
    1. Total cards: SELECT COUNT(*) FROM cards;
    2. Cards per trend_label: SELECT trend_label, COUNT(*) FROM cards GROUP BY trend_label;
    3. Newest update: SELECT MAX(last_updated) FROM cards;
    4. Cards by set (top 5): SELECT set_name, COUNT(*) FROM cards GROUP BY set_name ORDER BY COUNT(*) DESC LIMIT 5;
    5. Cards with no prices anywhere (data quality check):
       SELECT COUNT(*) FROM cards WHERE price_ebay IS NULL AND price_tcgplayer IS NULL;

    Print it as a formatted report.
    """
    print("\n=== CARD DATABASE SUMMARY ===")
    print(f"DB: {DB_NAME} in container: {DB_CONTAINER}\n")

    try:
        # TODO: Call db.query_one() for each stat above and print them
        # YOUR CODE HERE

        # For now, give you the structure:
        total = db.query_one("SELECT COUNT(*) FROM cards;")
        print(f"Total cards: {total or 'unavailable'}")

        # TODO: Add remaining queries
        # YOUR CODE HERE

    except RuntimeError as e:
        print(f"ERROR: {e}")
        print("Is nexusos-postgres running? Try: docker-compose up -d postgres")


def report_trending_cards(db: PokevengDB, limit: int = 10) -> None:
    """
    Show the top rising and falling cards.
    This is EXACTLY what card_store.go GetTrending() returns.

    card_store.go lines 128-135:
        GetTrending → rising = queryByLabel("RISING", "trending_score DESC")
                    → falling = queryByLabel("FALLING", "trending_score ASC")

    TODO:
    1. Query top 10 RISING cards:
       SELECT name, set_name, price_ebay, trending_score, pct_change_7d
       FROM cards WHERE trend_label='RISING'
       ORDER BY trending_score DESC LIMIT 10;

    2. Query top 10 FALLING cards:
       SELECT name, set_name, price_ebay, trending_score, pct_change_7d
       FROM cards WHERE trend_label='FALLING'
       ORDER BY trending_score ASC LIMIT 10;

    3. Print both tables nicely formatted.

    NOTE: pct_change_7d is the 7-day price change percentage.
         RISING + high pct_change_7d = hot card (buy opportunity for traders)
         FALLING + negative pct_change_7d = dropping card (sell signal)
    """
    print("\n=== TRENDING CARDS ===")
    print("(Mirrors what your API returns at GET /api/v1/cards/trending)\n")

    try:
        # TODO: Implement both RISING and FALLING queries
        # YOUR CODE HERE
        print("(Not implemented yet — complete the TODO above)")
    except RuntimeError as e:
        print(f"ERROR: {e}")


def report_price_analysis(db: PokevengDB) -> None:
    """
    Analyse prices across all 4 marketplaces.
    The card model has: price_ebay, price_tcgplayer, price_facebook, price_mercari

    TODO:
    1. Get all cards with at least one price:
       SELECT name, price_ebay, price_tcgplayer, price_facebook, price_mercari
       FROM cards
       WHERE price_ebay IS NOT NULL OR price_tcgplayer IS NOT NULL
       ORDER BY COALESCE(price_ebay, price_tcgplayer, 0) DESC
       LIMIT 20;

    2. Use Python's statistics module to calculate:
       - mean price per marketplace
       - median price per marketplace
       - max price (the most expensive card)
       - min price (the cheapest card with a price)

    3. Show marketplace coverage:
       How many cards have prices on each marketplace?
       SELECT
         COUNT(*) FILTER (WHERE price_ebay > 0) as ebay_count,
         COUNT(*) FILTER (WHERE price_tcgplayer > 0) as tcg_count,
         COUNT(*) FILTER (WHERE price_facebook > 0) as facebook_count,
         COUNT(*) FILTER (WHERE price_mercari > 0) as mercari_count
       FROM cards;

    4. Find arbitrage opportunities:
       Cards where eBay price is significantly higher than TCGPlayer
       (these are the most valuable for your pricing alerts feature)
       SELECT name, price_ebay, price_tcgplayer,
              (price_ebay - price_tcgplayer) as spread
       FROM cards
       WHERE price_ebay IS NOT NULL AND price_tcgplayer IS NOT NULL
         AND price_ebay > price_tcgplayer * 1.2
       ORDER BY spread DESC LIMIT 10;
    """
    print("\n=== PRICE ANALYSIS ===")
    print("(Shows real marketplace pricing data — powers your alerts feature)\n")

    try:
        # TODO: Implement all queries above
        # YOUR CODE HERE
        print("(Not implemented yet — complete the TODO above)")
    except RuntimeError as e:
        print(f"ERROR: {e}")


def search_cards(db: PokevengDB, query: str) -> None:
    """
    Replicate the EXACT search query from card_store.go Search() method.

    card_store.go lines 88-104:
        WHERE (name ILIKE $1 OR set_name ILIKE $1)
        searchPattern = fmt.Sprintf("%%%s%%", query)

    The %% pattern means ILIKE '%charizard%' → matches any card with
    "charizard" anywhere in the name, case-insensitive.

    TODO:
    1. Build the search pattern: f"%{query}%"
    2. Run the EXACT same SQL as card_store.go (without cursor pagination):
       SELECT card_id, name, set_name, price_ebay, price_tcgplayer, trending_score
       FROM cards
       WHERE name ILIKE '{pattern}' OR set_name ILIKE '{pattern}'
       ORDER BY card_id ASC LIMIT 20
    3. Print results as a table

    SECURITY NOTE: In Go, this uses parameterized queries ($1) to prevent
    SQL injection. In Python subprocess+psql, you must be careful.
    For this script, only accept alphanumeric + spaces in the query.

    Add this validation:
       if not all(c.isalnum() or c in ' -.' for c in query):
           raise ValueError(f"Invalid search query: {query}")
    """
    print(f"\n=== CARD SEARCH: '{query}' ===")
    print("(Mirrors GET /api/v1/cards/search?q=... from card_handler.go)\n")

    # Input validation FIRST (security)
    if not all(c.isalnum() or c in ' -.' for c in query):
        print(f"ERROR: Invalid search query '{query}'. Use letters, numbers, spaces only.")
        return

    try:
        # TODO: Implement the search
        # YOUR CODE HERE
        print("(Not implemented yet — complete the TODO above)")
    except RuntimeError as e:
        print(f"ERROR: {e}")


def export_cards_json(db: PokevengDB, output_path: Path) -> None:
    """
    Export all cards as JSON to a file.
    This is what you'd use to seed a test database or send data to an analyst.

    TODO:
    1. Query ALL cards: SELECT * FROM cards ORDER BY name;
       Use db.query_cards() to get dicts

    2. Add metadata to the export:
       {
         "exported_at": "2026-04-01T14:23:01",
         "total_cards": 1234,
         "source": "nexusos-postgres pokemontool DB",
         "cards": [ ... ]
       }

    3. Write to output_path using pathlib:
       output_path.write_text(json.dumps(data, indent=2, default=str))
       (default=str handles datetime objects that aren't JSON serializable)

    4. Print the file size after writing
    """
    print(f"\nExporting cards to: {output_path}")

    try:
        # TODO: Implement export
        # YOUR CODE HERE
        print("(Not implemented yet — complete the TODO above)")
    except RuntimeError as e:
        print(f"ERROR: {e}")


# =============================================================================
# CLI
# =============================================================================

def parse_args() -> argparse.Namespace:
    """
    TODO: Create argument parser with:
      --report REPORT   (choices: summary, trending, prices — default: summary)
      --query TEXT      (search query for --report search)
      --export PATH     (export all cards to this JSON file)
      --limit INT       (rows to show for trending/search, default: 10)
    """
    # YOUR CODE HERE
    # Temporary fallback
    class FakeArgs:
        report = "summary"
        query  = None
        export = None
        limit  = 10
    return FakeArgs()


def main() -> None:
    args   = parse_args()
    db     = PokevengDB()

    print("Pokevend DB Analyst")
    print(f"DB: {DB_NAME} | Container: {DB_CONTAINER}")

    if args.export:
        export_cards_json(db, Path(args.export))
        return

    report_map = {
        "summary":  lambda: report_card_summary(db),
        "trending": lambda: report_trending_cards(db, args.limit),
        "prices":   lambda: report_price_analysis(db),
        "search":   lambda: search_cards(db, args.query or "charizard"),
    }

    if args.report in report_map:
        report_map[args.report]()
    else:
        print(f"Unknown report: {args.report}")
        sys.exit(1)


if __name__ == "__main__":
    main()
