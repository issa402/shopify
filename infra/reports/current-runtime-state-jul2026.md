# Docker Compose Infrastructure Inventory

Repo: `/home/iscjmz/shopify/shopify`
Services found: `23`

## Compose Files

- `/home/iscjmz/shopify/shopify/docker-compose.yml` - checked
- `/home/iscjmz/shopify/shopify/docker-compose.odoo.yml` - checked
- `/home/iscjmz/shopify/shopify/Pokemon/docker-compose.yml` - checked

## Service Inventory

| Compose | Service | Runtime | Ports | Depends On | Volumes | Healthcheck |
|---|---|---|---|---|---|---|
| `docker-compose.yml` | `kafka` | `confluentinc/cp-kafka:7.7.0` | 9092:9092 | zookeeper | kafka_data:/var/lib/kafka/data | yes |
| `docker-compose.yml` | `ollama` | `ollama/ollama:latest` | 11434:11434 |  | ollama_data:/root/.ollama | no |
| `docker-compose.yml` | `postgres` | `pgvector/pgvector:pg16` | 5432:5432 |  | postgres_data:/var/lib/postgresql/data<br>./services/gateway/internal/db/migrations:/docker-entrypoint-initdb.d | yes |
| `docker-compose.yml` | `qdrant` | `qdrant/qdrant:latest` | 6333:6333<br>6334:6334 |  | qdrant_data:/qdrant/storage | yes |
| `docker-compose.yml` | `redis` | `redis:7-alpine` | 6379:6379 |  | redis_data:/data | yes |
| `docker-compose.yml` | `temporal` | `temporalio/auto-setup:1.24` | 7233:7233 | postgres | ./config/temporal/dynamicconfig.yaml:/etc/temporal/config/dynamicconfig.yaml:ro | no |
| `docker-compose.yml` | `temporal-ui` | `temporalio/ui:2.28.0` | 8088:8080 | temporal |  | no |
| `docker-compose.yml` | `zookeeper` | `confluentinc/cp-zookeeper:7.7.0` | 2181:2181 |  | zookeeper_data:/var/lib/zookeeper/data | no |
| `docker-compose.odoo.yml` | `odoo` | `odoo:19.0` | 127.0.0.1:${ODOO_HTTP_PORT:-8069}:8069<br>127.0.0.1:${ODOO_LONGPOLL_PORT:-8072}:8072 | odoo-db | odoo_data:/var/lib/odoo<br>./odoo/config/odoo.conf:/etc/odoo/odoo.conf:ro<br>./odoo/custom_addons:/mnt/extra-addons:ro | no |
| `docker-compose.odoo.yml` | `odoo-db` | `postgres:15-alpine` | 127.0.0.1:${ODOO_POSTGRES_PORT:-55432}:5432 |  | odoo_db_data:/var/lib/postgresql/data | yes |
| `Pokemon/docker-compose.yml` | `analytics-engine` | `./services/analytics-engine (Dockerfile)` |  | postgres<br>rabbitmq |  | no |
| `Pokemon/docker-compose.yml` | `api-consumer` | `./services/api-consumer (Dockerfile)` |  | postgres<br>rabbitmq |  | no |
| `Pokemon/docker-compose.yml` | `client` | `./client (Dockerfile)` | 5173:80 | server |  | no |
| `Pokemon/docker-compose.yml` | `grafana` | `grafana/grafana:latest` | 127.0.0.1:3000:3000 |  | grafanadata:/var/lib/grafana | no |
| `Pokemon/docker-compose.yml` | `loki` | `grafana/loki:2.9.0` | 127.0.0.1:3100:3100 |  |  | no |
| `Pokemon/docker-compose.yml` | `poketcg` | `../PokeTCG/pokeai-service/pokeai (Dockerfile)` | 127.0.0.1:8765:8765 |  |  | yes |
| `Pokemon/docker-compose.yml` | `postgres` | `postgres:15-alpine` | 127.0.0.1:5432:5432 |  | pgdata:/var/lib/postgresql/data<br>./database/migrations:/docker-entrypoint-initdb.d | yes |
| `Pokemon/docker-compose.yml` | `prometheus` | `prom/prometheus:v2.55.1` | 127.0.0.1:9090:9090 | server | ./prometheus.yml:/etc/prometheus/prometheus.yml:ro<br>prometheusdata:/prometheus | no |
| `Pokemon/docker-compose.yml` | `promtail` | `grafana/promtail:2.9.0` |  |  | /var/lib/docker/containers:/var/lib/docker/containers:ro<br>/var/run/docker.sock:/var/run/docker.sock<br>./promtail-config.yaml:/etc/promtail/config.yml | no |
| `Pokemon/docker-compose.yml` | `rabbitmq` | `rabbitmq:3-management-alpine` | 127.0.0.1:5672:5672<br>127.0.0.1:15672:15672 |  | rabbitmqdata:/var/lib/rabbitmq | yes |
| `Pokemon/docker-compose.yml` | `redis` | `redis:7-alpine` | 127.0.0.1:6379:6379 |  | redisdata:/data | yes |
| `Pokemon/docker-compose.yml` | `scraping-service` | `./services/scraping-service (Dockerfile)` |  | rabbitmq | playwright_browsers:/home/scrapeuser/.cache/ms-playwright<br>playwright_driver:/home/scrapeuser/.cache/ms-playwright-go | no |
| `Pokemon/docker-compose.yml` | `server` | `./server (Dockerfile)` | ${PORT:-3001}:3001 | poketcg<br>postgres<br>rabbitmq<br>redis |  | no |

## Risk Notes

### `kafka` from `docker-compose.yml`

- persistent/mounted data exists; backup/restore ownership matters
- env keys: `KAFKA_ADVERTISED_LISTENERS, KAFKA_AUTO_CREATE_TOPICS_ENABLE, KAFKA_BROKER_ID, KAFKA_INTER_BROKER_LISTENER_NAME, KAFKA_LISTENER_SECURITY_PROTOCOL_MAP, KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR, KAFKA_ZOOKEEPER_CONNECT`

### `ollama` from `docker-compose.yml`

- published port but no healthcheck in compose
- persistent/mounted data exists; backup/restore ownership matters

### `postgres` from `docker-compose.yml`

- review exposure: sensitive service publishes non-localhost port 5432:5432
- persistent/mounted data exists; backup/restore ownership matters
- secret-like env keys present: POSTGRES_PASSWORD
- env keys: `POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER`

### `qdrant` from `docker-compose.yml`

- persistent/mounted data exists; backup/restore ownership matters

### `redis` from `docker-compose.yml`

- review exposure: sensitive service publishes non-localhost port 6379:6379
- persistent/mounted data exists; backup/restore ownership matters

### `temporal` from `docker-compose.yml`

- published port but no healthcheck in compose
- persistent/mounted data exists; backup/restore ownership matters
- env keys: `DB, DB_PORT, DYNAMIC_CONFIG_FILE_PATH, POSTGRES_PWD, POSTGRES_SEEDS, POSTGRES_USER`

### `temporal-ui` from `docker-compose.yml`

- published port but no healthcheck in compose
- env keys: `TEMPORAL_ADDRESS`

### `zookeeper` from `docker-compose.yml`

- published port but no healthcheck in compose
- persistent/mounted data exists; backup/restore ownership matters
- env keys: `ZOOKEEPER_CLIENT_PORT, ZOOKEEPER_TICK_TIME`

### `odoo` from `docker-compose.odoo.yml`

- localhost-only port binding: 127.0.0.1:${ODOO_HTTP_PORT:-8069}:8069
- localhost-only port binding: 127.0.0.1:${ODOO_LONGPOLL_PORT:-8072}:8072
- published port but no healthcheck in compose
- persistent/mounted data exists; backup/restore ownership matters
- secret-like env keys present: PASSWORD
- env keys: `HOST, PASSWORD, USER`
- networks: `default, odoo-bridge`

### `odoo-db` from `docker-compose.odoo.yml`

- localhost-only port binding: 127.0.0.1:${ODOO_POSTGRES_PORT:-55432}:5432
- persistent/mounted data exists; backup/restore ownership matters
- secret-like env keys present: POSTGRES_PASSWORD
- env keys: `POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER`

### `analytics-engine` from `Pokemon/docker-compose.yml`

- no obvious first-pass risk from compose fields

### `api-consumer` from `Pokemon/docker-compose.yml`

- no obvious first-pass risk from compose fields
- env keys: `GO_INTERNAL_URL`

### `client` from `Pokemon/docker-compose.yml`

- published port but no healthcheck in compose

### `grafana` from `Pokemon/docker-compose.yml`

- localhost-only port binding: 127.0.0.1:3000:3000
- published port but no healthcheck in compose
- persistent/mounted data exists; backup/restore ownership matters
- secret-like env keys present: GF_SECURITY_ADMIN_PASSWORD
- env keys: `GF_SECURITY_ADMIN_PASSWORD`

### `loki` from `Pokemon/docker-compose.yml`

- localhost-only port binding: 127.0.0.1:3100:3100
- published port but no healthcheck in compose

### `poketcg` from `Pokemon/docker-compose.yml`

- localhost-only port binding: 127.0.0.1:8765:8765
- internal expose: `8765`

### `postgres` from `Pokemon/docker-compose.yml`

- localhost-only port binding: 127.0.0.1:5432:5432
- persistent/mounted data exists; backup/restore ownership matters
- secret-like env keys present: POSTGRES_PASSWORD
- env keys: `POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER`

### `prometheus` from `Pokemon/docker-compose.yml`

- localhost-only port binding: 127.0.0.1:9090:9090
- published port but no healthcheck in compose
- persistent/mounted data exists; backup/restore ownership matters

### `promtail` from `Pokemon/docker-compose.yml`

- persistent/mounted data exists; backup/restore ownership matters

### `rabbitmq` from `Pokemon/docker-compose.yml`

- localhost-only port binding: 127.0.0.1:5672:5672
- localhost-only port binding: 127.0.0.1:15672:15672
- persistent/mounted data exists; backup/restore ownership matters
- env keys: `RABBITMQ_DEFAULT_PASS, RABBITMQ_DEFAULT_USER`

### `redis` from `Pokemon/docker-compose.yml`

- localhost-only port binding: 127.0.0.1:6379:6379
- persistent/mounted data exists; backup/restore ownership matters

### `scraping-service` from `Pokemon/docker-compose.yml`

- persistent/mounted data exists; backup/restore ownership matters
- env keys: `DISPLAY`

### `server` from `Pokemon/docker-compose.yml`

- published port but no healthcheck in compose
- env keys: `API_CONSUMER_BASE_URL, ODOO_URL, POKETCG_BASE_URL`
- networks: `default, odoo-bridge`

## How To Use This Report

Use this report to decide what needs hardening before cloud deployment:

- Services with persistent volumes need backup/restore proof.
- Services with published ports need exposure review.
- Services without healthchecks need observability decisions.
- Secret-like env keys need production secret management.
- Localhost bindings map to private/internal exposure thinking in AWS.

