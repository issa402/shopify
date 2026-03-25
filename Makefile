# NexusOS 2026 — Developer Makefile
# Run from repo root: c:\Users\isjim\OneDrive\Desktop\shopify

.PHONY: help dev stop clean migrate agents test gateway ai web logs

# ─── Default ────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  NexusOS 2026 — Command Reference"
	@echo "  ─────────────────────────────────"
	@echo "  make dev        Start all services (infra + gateway + ai + web)"
	@echo "  make infra      Start infrastructure only (Postgres, Redis, Kafka, etc.)"
	@echo "  make stop       Stop all Docker containers"
	@echo "  make clean      Remove all Docker volumes (DATA LOSS WARNING)"
	@echo "  make migrate    Run DB migrations"
	@echo "  make gateway    Run Go gateway service locally"
	@echo "  make ai         Run Python AI service locally"
	@echo "  make web        Run React frontend locally"
	@echo "  make agents     Run CrewAI agent simulation"
	@echo "  make test       Run all service tests"
	@echo "  make logs       Tail all container logs"
	@echo "  make a2a-test   Send a mock A2A agent request"
	@echo ""

# ─── Infrastructure ──────────────────────────────────────────────────────────
infra:
	docker compose up -d postgres redis qdrant kafka zookeeper ollama temporal temporal-ui
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@docker compose ps

stop:
	docker compose stop

clean:
	@echo "WARNING: This will delete all data volumes!"
	docker compose down -v

logs:
	docker compose logs -f --tail=50

# ─── Database ────────────────────────────────────────────────────────────────
migrate:
	@echo "Running database migrations..."
	docker compose exec postgres psql -U nexusos -d nexusos -f /docker-entrypoint-initdb.d/001_create_extensions.sql || true
	docker compose exec postgres psql -U nexusos -d nexusos -f /docker-entrypoint-initdb.d/002_create_core_tables.sql || true
	docker compose exec postgres psql -U nexusos -d nexusos -f /docker-entrypoint-initdb.d/003_create_audit_tables.sql || true
	docker compose exec postgres psql -U nexusos -d nexusos -f /docker-entrypoint-initdb.d/004_rls_policies.sql || true
	@echo "Migrations complete."

# ─── Services ────────────────────────────────────────────────────────────────
gateway:
	cd services/gateway && go run ./main.go

ai:
	cd services/ai && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm run dev

# ─── Full Dev Stack ──────────────────────────────────────────────────────────
dev:
	@$(MAKE) infra
	@echo "Starting application services..."
	@echo "  Gateway: http://localhost:8080"
	@echo "  AI:      http://localhost:8000"
	@echo "  Web:     http://localhost:3000"
	@echo "  Qdrant:  http://localhost:6333/dashboard"
	@echo "  Temporal http://localhost:8088"

# ─── Testing ─────────────────────────────────────────────────────────────────
test:
	cd services/gateway && go test ./... -v -count=1
	cd services/ai && python -m pytest tests/ -v
	cd apps/web && npm test -- --watchAll=false

# ─── Agent Tools ─────────────────────────────────────────────────────────────
agents:
	cd services/ai && python -m agents.simulation

a2a-test:
	cd scripts && python test_a2a_agent.py
