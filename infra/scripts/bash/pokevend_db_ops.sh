#!/usr/bin/env bash
# =============================================================================
# SCRIPT: pokevend_db_ops.sh
# MODULE: Bash + Linux — Week 1/2
# TIES TO THESE REAL PROJECT FILES:
#   database/migrations/        — SQL files auto-run by postgres on first start
#   docker-compose.yml line 26  — ./database/migrations mounted as initdb.d
#   server/store/card_store.go  — the actual tables this operates on
#   services/analytics-engine/repositories/card_repo.py — Python side of same DB
#
# WHAT IT DOES (when complete):
#   Full database operations toolkit for the Pokevend PostgreSQL database.
#   backup, restore, migrate, seed, inspect — everything a database admin does.
#
# THE REAL DATABASE:
#   Container:  pokemontool_postgres
#   DB name:    pokemontool
#   User:       pokemontool_user
#   Tables:     cards, users, watchlists, alerts, price_alerts,
#               inventory, deals, shows, card_listings, price_history, api_keys
#
# HOW TO RUN:
#   bash infra/scripts/bash/pokevend_db_ops.sh backup
#   bash infra/scripts/bash/pokevend_db_ops.sh restore /tmp/backup.sql.gz
#   bash infra/scripts/bash/pokevend_db_ops.sh migrate
#   bash infra/scripts/bash/pokevend_db_ops.sh inspect
#   bash infra/scripts/bash/pokevend_db_ops.sh seed-test-data
#   bash infra/scripts/bash/pokevend_db_ops.sh reset   (⚠ WIPES ALL DATA)
#
# PREREQUISITE: Run through the output of each command manually first:
#   docker exec pokemontool_postgres psql -U pokemontool_user -d pokemontool -c "\dt"
# =============================================================================

set -euo pipefail

readonly PROJECT_ROOT="/home/iscjmz/shopify/shopify/Pokemon"
readonly CONTAINER="pokemontool_postgres"
readonly DB_NAME="${POSTGRES_DB:-pokemontool}"
readonly DB_USER="${POSTGRES_USER:-pokemontool_user}"
readonly MIGRATIONS_DIR="${PROJECT_ROOT}/database/migrations"
readonly SEEDS_DIR="${PROJECT_ROOT}/database/seeds"
readonly BACKUP_DIR="${HOME}/pokevend_backups"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'; BOLD='\033[1m'
ok()   { echo -e "  ${GREEN}✓${NC} $*"; }
fail() { echo -e "  ${RED}✗${NC} $*"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $*"; }

# =============================================================================
# HELPER: run psql inside the container
# This is the CORE pattern — learn it, use it everywhere
# =============================================================================
psql_exec() {
    # Runs a SQL command inside the pokemontool_postgres container
    # Usage: psql_exec "SELECT COUNT(*) FROM cards;"
    # Returns: printed output from psql
    docker exec "${CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" "$@"
}

psql_query() {
    # Runs a SQL query and returns result as clean text (no headers, no borders)
    # -t = tuples only (no column headers)
    # -A = unaligned (no padding spaces)
    # Usage: count=$(psql_query -c "SELECT COUNT(*) FROM cards;")
    docker exec "${CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -tA "$@"
}

# =============================================================================
# COMMAND: backup
# Creates a timestamped, compressed SQL dump of the entire database
# =============================================================================
cmd_backup() {
    echo ""
    echo -e "${BOLD}═══ DATABASE BACKUP ═══${NC}"
    echo "  Database: ${DB_NAME} | Container: ${CONTAINER}"

    # TODO: Verify postgres is running before attempting backup
    # HINT: docker exec "${CONTAINER}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" &>/dev/null
    # If it fails: print error and exit 1
    # YOUR CODE HERE

    # TODO: Create backup directory if it doesn't exist
    # COMMAND: mkdir -p "${BACKUP_DIR}"
    # YOUR CODE HERE

    # Build the backup filename with timestamp
    local timestamp; timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/pokevend_${DB_NAME}_${timestamp}.sql"
    local compressed="${backup_file}.gz"

    # TODO: Run pg_dump INSIDE the container and save to the backup file
    # pg_dump flags:
    #   -U username    — database user
    #   -d dbname      — database name
    #   --no-password  — don't prompt (we're running as postgres user in container)
    #   --clean        — add DROP statements (makes restore idempotent)
    #   --if-exists    — skip DROP errors if tables don't exist
    # COMMAND: docker exec "${CONTAINER}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" \
    #          --no-password --clean --if-exists > "${backup_file}"
    # YOUR CODE HERE

    # TODO: Compress the backup with gzip
    # COMMAND: gzip "${backup_file}"
    # Why: SQL dumps can be 10x smaller when compressed
    # YOUR CODE HERE

    # TODO: Print the backup size
    # COMMAND: du -sh "${compressed}"
    # YOUR CODE HERE

    # TODO: Verify the backup is not empty (gzip -t checks integrity)
    # COMMAND: gzip -t "${compressed}" && echo "✓ Backup integrity OK"
    # YOUR CODE HERE

    # TODO: Prune old backups — keep only the last 7
    # COMMAND: ls -t "${BACKUP_DIR}"/pokevend_*.sql.gz | tail -n +8 | xargs rm -f
    # WHY: Backups accumulate. 7 daily backups = 1 week of recovery options.
    # The Grandfather-Father-Son strategy keeps more granular recent backups.
    # YOUR CODE HERE

    echo ""
    ok "Backup saved to: ${compressed}"
}

# =============================================================================
# COMMAND: restore
# Restores from a .sql.gz backup file
# =============================================================================
cmd_restore() {
    local backup_file="${1:-}"

    echo ""
    echo -e "${BOLD}═══ DATABASE RESTORE ═══${NC}"

    # TODO: Validate that a backup file was provided and exists
    # [[ -z "${backup_file}" ]] → print usage and exit 1
    # [[ ! -f "${backup_file}" ]] → print "file not found" and exit 1
    # YOUR CODE HERE

    # SAFETY: Require explicit confirmation before wiping the database
    echo ""
    warn "This will WIPE and RESTORE the database from:"
    warn "  ${backup_file}"
    warn "All current data will be DELETED."
    echo ""
    read -rp "Type 'RESTORE' to confirm: " confirmation
    [[ "${confirmation}" == "RESTORE" ]] || { echo "Cancelled."; exit 1; }

    # TODO: Decompress the backup and pipe it into psql
    # COMMAND: zcat "${backup_file}" | docker exec -i "${CONTAINER}" \
    #          psql -U "${DB_USER}" -d "${DB_NAME}" --no-password
    # -i flag on docker exec = interactive (allow stdin pipe)
    # zcat = decompress and print to stdout (works with .gz files)
    # YOUR CODE HERE

    # TODO: Verify restore succeeded by counting rows in cards table
    # YOUR CODE HERE

    ok "Restore complete"
}

# =============================================================================
# COMMAND: migrate
# Applies any new SQL migration files from database/migrations/
# docker-compose.yml auto-runs these on FIRST start, but not after.
# This command handles subsequent migrations manually.
# =============================================================================
cmd_migrate() {
    echo ""
    echo -e "${BOLD}═══ DATABASE MIGRATIONS ═══${NC}"
    echo "  Migrations dir: ${MIGRATIONS_DIR}"

    # TODO: Verify the migrations directory exists
    # YOUR CODE HERE

    # TODO: List all .sql files in the migrations directory, sorted
    # COMMAND: ls -1 "${MIGRATIONS_DIR}"/*.sql 2>/dev/null | sort
    # Sort ensures migrations run in the right order
    # (Convention: files are named 001_init.sql, 002_add_deals.sql, etc.)
    # YOUR CODE HERE

    # TODO: Create a migrations tracking table if it doesn't exist
    # This table records which migrations have already been applied
    # SQL:
    #   CREATE TABLE IF NOT EXISTS schema_migrations (
    #       version    TEXT PRIMARY KEY,
    #       applied_at TIMESTAMPTZ DEFAULT NOW()
    #   );
    # COMMAND: psql_query -c "CREATE TABLE IF NOT EXISTS schema_migrations ..."
    # YOUR CODE HERE

    # TODO: For each .sql file (sorted):
    #   1. Extract the filename (basename from the full path)
    #   2. Check if it's already in schema_migrations:
    #      SELECT COUNT(*) FROM schema_migrations WHERE version = 'filename.sql'
    #   3. If count == 0: apply it and record it
    #      APPLY:  docker exec -i "${CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" < "${sql_file}"
    #      RECORD: psql_query -c "INSERT INTO schema_migrations (version) VALUES ('filename.sql');"
    #   4. If count > 0: skip it
    # YOUR CODE HERE

    echo ""
    ok "All migrations applied"
}

# =============================================================================
# COMMAND: inspect
# Shows a detailed snapshot of what's in the database right now
# Essential for debugging: "why is the frontend showing wrong data?"
# =============================================================================
cmd_inspect() {
    echo ""
    echo -e "${BOLD}═══ DATABASE INSPECTION ═══${NC}"
    echo "  DB: ${DB_NAME} | $(date '+%Y-%m-%d %H:%M:%S')"

    # TODO: List all tables with row counts
    # SQL: SELECT table_name, (SELECT COUNT(*) FROM information_schema.tables t2
    #      WHERE t2.table_name = t.table_name) FROM information_schema.tables t
    #      WHERE table_schema = 'public'
    # SIMPLER: Build a shell loop that runs COUNT(*) for each table
    # Get table list: psql_query -c "\dt" | awk -F'|' '{print $2}' | tr -d ' '
    # Then for each: psql_query -c "SELECT COUNT(*) FROM ${table};"
    # YOUR CODE HERE

    echo ""

    # TODO: Show most recent 5 cards (highest last_updated)
    # SQL: SELECT name, price_ebay, price_tcgplayer, last_updated
    #      FROM cards ORDER BY last_updated DESC LIMIT 5;
    # This tells you when the scraper last ran successfully
    # YOUR CODE HERE

    # TODO: Show top 5 trending cards (highest trending_score)
    # SQL: SELECT name, trend_label, trending_score, pct_change_7d
    #      FROM cards WHERE trend_label = 'RISING'
    #      ORDER BY trending_score DESC LIMIT 5;
    # These are the cards shown on the frontend dashboard
    # YOUR CODE HERE

    # TODO: Show today's deals
    # SQL: SELECT card_name, marketplace, original_price, deal_price, discount_pct
    #      FROM deals
    #      WHERE created_at::date = CURRENT_DATE
    #      ORDER BY discount_pct DESC LIMIT 5;
    # If no results and it's after 6 AM: analytics engine deal_finder may not have run
    # YOUR CODE HERE

    # TODO: Show active watchlists (what users are monitoring)
    # SQL: SELECT card_name, COUNT(*) as watcher_count
    #      FROM watchlists GROUP BY card_name ORDER BY watcher_count DESC LIMIT 10;
    # This drives the api-consumer scanner_loop — these are the cards it scans
    # YOUR CODE HERE

    # TODO: Show database size breakdown
    # SQL: SELECT table_name,
    #             pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
    #      FROM information_schema.tables WHERE table_schema = 'public'
    #      ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;
    # YOUR CODE HERE
}

# =============================================================================
# COMMAND: seed-test-data
# Inserts realistic test data so you can test the Go API locally
# without needing the scrapers to have run
# =============================================================================
cmd_seed() {
    echo ""
    echo -e "${BOLD}═══ SEED TEST DATA ═══${NC}"

    warn "This inserts TEST data into ${DB_NAME}"
    warn "Existing data will NOT be affected (INSERT uses ON CONFLICT DO NOTHING)"

    # TODO: Insert seed Pokémon cards if the cards table is empty
    # (If already populated by the scraper, skip — don't overwrite real data)
    local card_count
    card_count=$(psql_query -c "SELECT COUNT(*) FROM cards;" 2>/dev/null | tr -d ' ') || card_count="0"

    if [[ "${card_count}" -gt 100 ]]; then
        ok "Cards table already has ${card_count} rows — skipping card seed"
    else
        echo "  Inserting test cards..."
        # TODO: Use a heredoc to INSERT realistic test cards
        # SQL example:
        # INSERT INTO cards (card_id, name, set_name, set_code, price_ebay, price_tcgplayer,
        #                    trending_score, trend_label, pct_change_7d, last_updated)
        # VALUES
        #   ('base1-4',   'Charizard',  'Base Set',   'base1',  450.00, 420.00, 85, 'RISING',  12.5, NOW()),
        #   ('base1-2',   'Blastoise',  'Base Set',   'base1',  180.00, 165.00, 45, 'RISING',   8.2, NOW()),
        #   ('base1-1',   'Bulbasaur',  'Base Set',   'base1',   25.00,  22.00, -20,'FALLING', -9.1, NOW()),
        #   ('cel25-25',  'Pikachu',    'Celebrations','cel25',  35.00,  30.00,  0, 'STABLE',   1.2, NOW())
        # ON CONFLICT (card_id) DO NOTHING;
        # COMMAND: psql_exec -c "INSERT INTO cards ..."
        # YOUR CODE HERE
        echo "  (INSERT statement not implemented — add test cards above)"
    fi

    # TODO: Insert a test user (so you can test login)
    # The users table stores hashed passwords — use a known hash for test password "Password123!"
    # SQL: INSERT INTO users (email, password_hash, created_at)
    #      VALUES ('test@pokevend.com', '..hashed..', NOW()) ON CONFLICT DO NOTHING;
    # NOTE: Don't store a real password. Use bcrypt hash of a test password.
    # You can get one: docker exec pokemontool_server <run a Go test> or use htpasswd
    # YOUR CODE HERE

    # TODO: Insert test watchlists for the test user
    # This drives the api-consumer scanner_loop (it reads from watchlists table)
    # SQL: INSERT INTO watchlists (user_id, card_name) VALUES (1, 'Charizard') ON CONFLICT DO NOTHING;
    # YOUR CODE HERE

    ok "Test data seeded"
}

# =============================================================================
# COMMAND: reset
# DANGEROUS: drops all tables and re-runs migrations from scratch
# Only use in development. NEVER in production.
# =============================================================================
cmd_reset() {
    echo ""
    echo -e "${RED}${BOLD}═══ DATABASE RESET (DESTRUCTIVE) ═══${NC}"

    warn "THIS WILL DELETE EVERY ROW IN EVERY TABLE"
    warn "Use only in development. Never on production."
    echo ""
    read -rp "Type 'DELETE EVERYTHING' to confirm: " confirmation
    [[ "${confirmation}" == "DELETE EVERYTHING" ]] || { echo "Cancelled."; exit 1; }

    # TODO: Drop all tables by dropping and recreating the schema
    # Safest approach: DROP SCHEMA public CASCADE; CREATE SCHEMA public;
    # This removes everything without affecting the postgres user permissions
    # COMMAND: psql_exec -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    # YOUR CODE HERE

    # TODO: Re-run all migrations from scratch
    cmd_migrate

    # TODO: Optionally re-seed test data
    read -rp "Seed test data? [y/N]: " seed_confirm
    [[ "${seed_confirm}" == "y" ]] && cmd_seed

    ok "Database reset complete"
}

# =============================================================================
# MAIN: Route subcommand
# =============================================================================
usage() {
    echo ""
    echo "Usage: $0 <command> [args]"
    echo ""
    echo "Commands:"
    echo "  backup              Create a timestamped backup"
    echo "  restore <file.gz>   Restore from backup file"
    echo "  migrate             Apply pending migrations"
    echo "  inspect             Show database contents summary"
    echo "  seed-test-data      Insert test cards, users, watchlists"
    echo "  reset               ⚠ WIPE and re-migrate (dev only)"
    echo ""
    echo "Examples:"
    echo "  $0 backup"
    echo "  $0 restore ~/pokevend_backups/pokevend_20260401.sql.gz"
    echo "  $0 inspect"
}

main() {
    local cmd="${1:-help}"
    shift 2>/dev/null || true

    case "${cmd}" in
        backup)         cmd_backup ;;
        restore)        cmd_restore "$@" ;;
        migrate)        cmd_migrate ;;
        inspect)        cmd_inspect ;;
        seed-test-data) cmd_seed ;;
        reset)          cmd_reset ;;
        help|--help|-h) usage ;;
        *)
            fail "Unknown command: ${cmd}"
            usage
            exit 1
            ;;
    esac
}

main "$@"
