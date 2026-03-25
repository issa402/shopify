// Package db manages PostgreSQL connections and migrations for NexusOS Gateway.
package db

import (
	"context"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Connect creates a pgx connection pool to Postgres.
func Connect(databaseURL string) (*pgxpool.Pool, error) {
	if databaseURL == "" {
		return nil, fmt.Errorf("DATABASE_URL is required")
	}

	config, err := pgxpool.ParseConfig(databaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse DATABASE_URL: %w", err)
	}

	config.MaxConns = 20
	config.MinConns = 2

	pool, err := pgxpool.NewWithConfig(context.Background(), config)
	if err != nil {
		return nil, fmt.Errorf("failed to create connection pool: %w", err)
	}

	// Verify connection
	if err := pool.Ping(context.Background()); err != nil {
		return nil, fmt.Errorf("database ping failed: %w", err)
	}

	log.Printf("[db] Connected to Postgres (max_conns=%d)", config.MaxConns)
	return pool, nil
}

// RunMigrations runs all SQL migration files in order.
func RunMigrations(pool *pgxpool.Pool) error {
	migrationsDir := "./internal/db/migrations"

	entries, err := os.ReadDir(migrationsDir)
	if err != nil {
		return fmt.Errorf("failed to read migrations dir: %w", err)
	}

	// Sort files to ensure order: 001, 002, 003, 004
	var files []string
	for _, e := range entries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".sql") {
			files = append(files, e.Name())
		}
	}
	sort.Strings(files)

	for _, filename := range files {
		path := filepath.Join(migrationsDir, filename)
		content, err := os.ReadFile(path)
		if err != nil {
			return fmt.Errorf("failed to read migration %s: %w", filename, err)
		}

		_, err = pool.Exec(context.Background(), string(content))
		if err != nil {
			// Log but don't fail on "already exists" errors (idempotent migrations)
			if strings.Contains(err.Error(), "already exists") {
				log.Printf("[db] Migration %s: skipped (already applied)", filename)
				continue
			}
			return fmt.Errorf("migration %s failed: %w", filename, err)
		}

		log.Printf("[db] Migration applied: %s", filename)
	}

	return nil
}

// SetMerchantContext sets the Postgres RLS session variable for data isolation.
// This must be called before any data query within a request context.
func SetMerchantContext(ctx context.Context, pool *pgxpool.Pool, merchantID string) error {
	_, err := pool.Exec(ctx, `SELECT set_config('app.current_merchant_id', $1, TRUE)`, merchantID)
	return err
}
