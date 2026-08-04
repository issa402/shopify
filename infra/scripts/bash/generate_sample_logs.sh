#!/usr/bin/env bash
# ============================================================
# generate_sample_logs.sh
# Creates REALISTIC sample logs for your Pokemon project
# RUN THIS FIRST: bash generate_sample_logs.sh
# Then use the generated logs for grep/awk/sed practice
# ============================================================

set -euo pipefail

LOG_DIR="/tmp/pokevend_logs"
mkdir -p "${LOG_DIR}"

echo "📝 Generating sample logs in ${LOG_DIR}/"
echo ""

# ============================================================
# 1. Go API Server Logs (app.log)
# Similar to what your pokemontool Go server would produce
# ============================================================
cat > "${LOG_DIR}/app.log" << 'EOF'
[2026-04-01T14:00:01Z] [INFO]  Server starting on port 3001
[2026-04-01T14:00:02Z] [INFO]  DB connection established: pokemontool_user@localhost:5432
[2026-04-01T14:00:03Z] [INFO]  Redis connected: localhost:6379
[2026-04-01T14:00:04Z] [DEBUG] GET /health → 200 OK (1ms)
[2026-04-01T14:00:05Z] [INFO]  GET /api/v1/cards → 200 OK (45ms) - User: user_123
[2026-04-01T14:00:06Z] [INFO]  GET /api/v1/watchlist → 200 OK (23ms) - User: user_456
[2026-04-01T14:00:07Z] [ERROR] POST /api/v1/cards → 500 Internal Server Error (234ms)
[2026-04-01T14:00:07Z] [ERROR] panic: nil pointer dereference in CardService.CreateCard()
[2026-04-01T14:00:08Z] [WARN]  DB connection timeout - retrying...
[2026-04-01T14:00:09Z] [INFO]  DB connection restored
[2026-04-01T14:00:10Z] [ERROR] PUT /api/v1/watchlist/999 → 404 Not Found (12ms) - Card not found
[2026-04-01T14:00:11Z] [INFO]  GET /api/v1/users/user_123/watchlist → 200 OK (67ms)
[2026-04-01T14:00:12Z] [WARN]  Slow query detected: SELECT ... from cards took 523ms
[2026-04-01T14:00:13Z] [DEBUG] Cache hit: watchlist_user_123 (1ms)
[2026-04-01T14:00:14Z] [INFO]  GET /api/v1/cards → 200 OK (34ms) - User: user_789
[2026-04-01T14:00:15Z] [ERROR] FATAL: Redis connection lost
[2026-04-01T14:00:16Z] [INFO]  Attempting Redis reconnection...
[2026-04-01T14:00:17Z] [INFO]  Redis reconnected
[2026-04-01T14:00:18Z] [DEBUG] POST /api/v1/cards → 201 Created (89ms)
[2026-04-01T14:00:19Z] [INFO]  Goroutine leak detected: 150 active (threshold: 100)
[2026-04-01T14:00:20Z] [ERROR] Worker job failed: process_price_alert (attempt 1/3)
[2026-04-01T14:00:21Z] [INFO]  Worker job retry: process_price_alert (attempt 2/3)
[2026-04-01T14:00:22Z] [INFO]  Worker job succeeded: process_price_alert
EOF

echo "✓ Created app.log (Go API server logs)"

# ============================================================
# 2. Nginx Access Logs (access.log)
# Similar to nginx reverse proxy in front of your services
# ============================================================
cat > "${LOG_DIR}/access.log" << 'EOF'
192.168.1.10 - user_123 [01/Apr/2026:14:00:05 +0000] "GET /api/v1/cards HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
192.168.1.11 - user_456 [01/Apr/2026:14:00:06 +0000] "GET /api/v1/watchlist HTTP/1.1" 200 567 "-" "Mozilla/5.0"
192.168.1.10 - user_123 [01/Apr/2026:14:00:07 +0000] "POST /api/v1/cards HTTP/1.1" 500 0 "-" "curl/7.64.1"
192.168.1.12 - user_999 [01/Apr/2026:14:00:08 +0000] "GET /api/v1/cards HTTP/1.1" 200 2345 "-" "Mozilla/5.0"
192.168.1.10 - user_123 [01/Apr/2026:14:00:09 +0000] "PUT /api/v1/watchlist/999 HTTP/1.1" 404 0 "-" "curl/7.64.1"
192.168.1.13 - user_777 [01/Apr/2026:14:00:10 +0000] "GET /api/v1/users/user_123/watchlist HTTP/1.1" 200 890 "-" "Mozilla/5.0"
192.168.1.11 - user_456 [01/Apr/2026:14:00:11 +0000] "GET /api/v1/cards HTTP/1.1" 200 1456 "-" "Mozilla/5.0"
192.168.1.14 - - [01/Apr/2026:14:00:12 +0000] "GET /health HTTP/1.1" 200 45 "-" "curl/7.64.1"
192.168.1.15 - attacker [01/Apr/2026:14:00:13 +0000] "POST /api/v1/admin/delete HTTP/1.1" 401 0 "-" "curl/7.64.1"
192.168.1.10 - user_123 [01/Apr/2026:14:00:14 +0000] "GET /api/v1/cards HTTP/1.1" 200 1123 "-" "Mozilla/5.0"
192.168.1.16 - scanner [01/Apr/2026:14:00:15 +0000] "GET /admin.php HTTP/1.1" 404 0 "-" "python-requests"
192.168.1.16 - scanner [01/Apr/2026:14:00:16 +0000] "GET /wp-admin/ HTTP/1.1" 404 0 "-" "python-requests"
192.168.1.10 - user_123 [01/Apr/2026:14:00:17 +0000] "POST /api/v1/cards HTTP/1.1" 201 234 "-" "curl/7.64.1"
192.168.1.11 - user_456 [01/Apr/2026:14:00:18 +0000] "GET /api/v1/watchlist HTTP/1.1" 200 678 "-" "Mozilla/5.0"
192.168.1.17 - - [01/Apr/2026:14:00:19 +0000] "GET / HTTP/1.1" 200 1024 "-" "curl/7.64.1"
EOF

echo "✓ Created access.log (Nginx reverse proxy logs)"

# ============================================================
# 3. Docker Error Logs (docker.log)
# Errors from your containers
# ============================================================
cat > "${LOG_DIR}/docker.log" << 'EOF'
[2026-04-01T14:00:01Z] Container pokemontool_postgres started
[2026-04-01T14:00:02Z] Container pokemontool_redis started
[2026-04-01T14:00:03Z] Container pokemontool_api started
[2026-04-01T14:00:04Z] ERROR: pokemontool_postgres: connection refused
[2026-04-01T14:00:05Z] Container pokemontool_postgres restarted
[2026-04-01T14:00:06Z] WARNING: pokemontool_redis: memory usage at 87%
[2026-04-01T14:00:07Z] ERROR: pokemontool_api: out of memory
[2026-04-01T14:00:08Z] Container pokemontool_api stopped
[2026-04-01T14:00:09Z] Container pokemontool_api started
[2026-04-01T14:00:10Z] INFO: All containers healthy
EOF

echo "✓ Created docker.log (Container logs)"

# ============================================================
# 4. Database Slow Query Log (slow_queries.log)
# ============================================================  
cat > "${LOG_DIR}/slow_queries.log" << 'EOF'
[2026-04-01 14:00:05.234] SLOW QUERY (523ms): SELECT * FROM cards WHERE user_id = ?
[2026-04-01 14:00:12.567] SLOW QUERY (687ms): SELECT * FROM watchlist WHERE ... (complex join)
[2026-04-01 14:00:18.123] SLOW QUERY (1234ms): SELECT * FROM users ... (N+1 query problem!)
[2026-04-01 14:00:25.456] SLOW QUERY (456ms): UPDATE cards SET price = ? WHERE id IN (...)
EOF

echo "✓ Created slow_queries.log (Database slow queries)"

echo ""
echo "✅ All sample logs created in: ${LOG_DIR}/"
echo ""
echo "Now you can practice grep/awk/sed:"
echo ""
echo "  grep 'ERROR' ${LOG_DIR}/app.log"
echo "  grep -c '200' ${LOG_DIR}/access.log"
echo "  awk '{print \$1}' ${LOG_DIR}/access.log | sort | uniq -c"
echo "  grep 'SLOW' ${LOG_DIR}/slow_queries.log"
echo ""
echo "🎯 Copy these examples into your lesson to make them WORK!"
