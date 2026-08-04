# 🗺️ POKEVEND INFRASTRUCTURE MASTERY — MASTER INDEX
## Complete map of every script, lesson, and task · Updated for the real project

---

## THE REAL STACK (Updated — Read This First)

```
Pokemon/
├── server/                      ← Go API (main.go — port 3001)
│   ├── config/config.go         ← env vars, DB connections, Validate()
│   ├── handlers/                ← HTTP layer (health, cards, auth, alerts...)
│   ├── services/                ← business logic (card_service, deal_service...)
│   ├── store/                   ← SQL queries (card_store, user_store...)
│   └── worker/                  ← RabbitMQ consumer → SSE push
│
├── services/
│   ├── api-consumer/            ← Python FastAPI (port 8001) — eBay + TCGplayer
│   │   ├── main.py              ← FastAPI + scanner_loop() background task
│   │   ├── repositories/        ← raw API calls (ebay_repo, tcg_repo)
│   │   ├── services/            ← business logic (ebay_service, tcg_service)
│   │   └── publisher/           ← RabbitMQ publisher
│   │
│   ├── analytics-engine/        ← Python batch service — trends + deals
│   │   ├── main.py              ← schedule library — runs hourly/daily
│   │   ├── trend_analyzer.py    ← 7d/30d moving avg → RISING/FALLING/STABLE
│   │   ├── analyzers/           ← deal_finder, news_scanner
│   │   └── repositories/        ← card_repo, listing_repo
│   │
│   └── scraping-service/        ← Go — Facebook Marketplace + Mercari (Playwright)
│
├── database/
│   ├── migrations/              ← SQL files auto-run on postgres startup
│   └── seeds/                   ← Test data
│
├── client/                      ← React frontend (port 5173)
└── docker-compose.yml           ← THE TRUTH — all containers, ports, deps

REAL CONTAINER NAMES (from docker-compose.yml):
  pokemontool_postgres   → port 5432
  pokemontool_redis      → port 6379
  pokemontool_rabbitmq   → port 5672 (AMQP), 15672 (Management UI)
  pokemontool_server     → port 3001 (Go API)
  pokemontool_api_consumer → port 8001 (FastAPI)
  pokemontool_analytics  → no public port (batch only)
  pokemontool_scraper    → no public port (headless browser)
  pokemontool_client     → port 5173 (React/Nginx)
```

---

## START HERE EVERY SESSION

```bash
# Morning startup — start the whole stack
cd /home/iscjmz/shopify/shopify/Pokemon
docker-compose up -d

# Confirm everything is running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check the Go API health endpoint
curl -s http://localhost:3001/health | python3 -m json.tool

# Check the FastAPI consumer health
curl -s http://localhost:8001/health | python3 -m json.tool

# Watch RabbitMQ: are messages flowing between services?
# Open in browser: http://localhost:15672 (guest/guest)
```

---

## ALL SCRIPTS — Complete Index

### 🐧 Linux / Docker Admin
| Script | What You Build | Status |
|--------|---------------|--------|
| `infra/scripts/linux/pokevend_stack_audit.sh` | Full audit of all 8 containers, DB, Redis, security | **Your TODOs** |
| `infra/scripts/linux/01_os_audit.sh` | OS-level audit (processes, memory, disk) | **Your TODOs** |
| `infra/scripts/linux/02_process_manager.sh` | systemd + docker service manager | **Your TODOs** |

### 🐚 Bash Scripting
| Script | What You Build | Status |
|--------|---------------|--------|
| `infra/scripts/bash/pokevend_log_parser.sh` | Parse chi + slog + RabbitMQ logs | **Your TODOs** |
| `infra/scripts/bash/pokevend_db_ops.sh` | Full DB backup/restore/migrate workflow | **Your TODOs** |
| `infra/scripts/bash/pokevend_deploy.sh` | Zero-downtime deployment of Go API + Python services | **Your TODOs** |

### 🐍 Python Scripting
| Script | What You Build | Status |
|--------|---------------|--------|
| `infra/scripts/python/pokevend_health_monitor.py` | Poll all 8 services, track uptime, write status page | **Your TODOs** |
| `infra/scripts/python/pokevend_db_analyst.py` | Query cards/deals/watchlists — like card_store.go in Python | **Your TODOs** |
| `infra/scripts/python/pokevend_config_validator.py` | Validate .env against config.go rules | **Your TODOs** |
| `infra/scripts/python/pokevend_rabbitmq_monitor.py` | Watch RabbitMQ queues, detect backlogs | **Your TODOs** |
| `infra/scripts/python/pokevend_trend_backtest.py` | Run trend_analyzer.py logic on historical data | **Your TODOs** |

### 🌐 Networking
| Script | What You Build | Status |
|--------|---------------|--------|
| `infra/scripts/network/pokevend_network_check.sh` | Port scan, CORS, rate limit test | **Your TODOs** |

### 🔒 Security
| Script | What You Build | Status |
|--------|---------------|--------|
| `infra/scripts/security/pokevend_secrets_audit.sh` | Scan all services for leaked keys/tokens | **Your TODOs** |

---

## LEARNING ORDER

### Week 1: Linux + Docker (do this first)
1. **READ** `infra/lessons/BASH_POKEVEND.md` — bash with real project examples
2. **IMPLEMENT** `infra/scripts/linux/pokevend_stack_audit.sh` — start easy (port checks)
3. **RUN** every `docker exec` command in the stack audit manually first
4. **IMPLEMENT** `infra/scripts/bash/pokevend_db_ops.sh` — backup/restore the real DB

### Week 2: Python + Automation
1. **READ** `infra/lessons/PYTHON_POKEVEND.md` — python with real project examples
2. **IMPLEMENT** `infra/scripts/python/pokevend_health_monitor.py` — socket + http checks
3. **IMPLEMENT** `infra/scripts/python/pokevend_db_analyst.py` — SQL via subprocess
4. **IMPLEMENT** `infra/scripts/python/pokevend_rabbitmq_monitor.py` — queue depth checks
5. **IMPLEMENT** the TODOs in `services/api-consumer/main.py` and `repositories/tcg_repo.py`

### Week 3: Networking
1. **IMPLEMENT** `infra/scripts/network/pokevend_network_check.sh`
2. **TEST** CORS by running the React app and watching network tab
3. **TEST** rate limiter by writing the 110-request bash loop

### Week 4: Security
1. **IMPLEMENT** `infra/scripts/security/pokevend_secrets_audit.sh`
2. **IMPLEMENT** `infra/scripts/python/pokevend_config_validator.py`
3. **RUN** `--generate` flag to create a hardened .env

### Week 5: Deployment
1. **IMPLEMENT** `infra/scripts/bash/pokevend_deploy.sh`
2. **READ** `Pokemon/aws_deployment_guide.md`
3. **UNDERSTAND** `Pokemon/docker-compose.prod.yml` — production differences

---

## HOW TO KNOW YOU'RE DONE WITH EACH SCRIPT
Every script has TODO markers. You're done when:
- Running the script with no arguments produces real output (not "NOT IMPLEMENTED")
- You can explain every line out loud
- You've run it at least 3 times with different inputs/states
- You've intentionally broken something and used the script to diagnose it
