# 📚 LESSON 03: Networking & Protocol Fundamentals
## MASTER REFERENCE — Read before touching any Week 3 scripts

---

## 🧠 The Mental Model: Networks Are Pipes

Imagine your Go backend is a person in a room. Networking is the system of pipes and doors that lets them talk to the world. To secure and troubleshoot it, you need to understand exactly which pipes exist, what travels through them, and who is allowed to open each door.

---

## 📡 PART 1: The OSI Model — The 7-Layer Framework

This is the single most important networking concept. Every engineer recites it. Every protocol lives at a specific layer.

```
Layer 7: Application  — HTTP, HTTPS, WebSocket, gRPC, DNS, SSH
Layer 6: Presentation — TLS/SSL (encryption), compression
Layer 5: Session      — Connection lifecycle management
Layer 4: Transport    — TCP, UDP (ports live here!)
Layer 3: Network      — IP addresses, routing (where do packets go?)
Layer 2: Data Link    — MAC addresses, switches (local network delivery)
Layer 1: Physical     — Cables, Wi-Fi, fiber (the actual hardware)
```

**Why this matters for Pokevend:**
- When Nginx receives an HTTPS request → It terminates TLS at Layer 6
- It forwards HTTP to Go at Layer 7
- Go connects to PostgreSQL at Layer 4 (TCP port 5432)
- PostgreSQL talks over Layer 3 (IP 127.0.0.1 or a Docker network)

**Troubleshooting shortcut**: Always debug from the bottom up. If Layer 3 (IP) is broken, Layer 7 (HTTP) will NEVER work.

---

## 🔌 PART 2: TCP vs UDP — The Two Transport Protocols

```
TCP (Transmission Control Protocol):
├── Connection-oriented — must "handshake" before talking (SYN, SYN-ACK, ACK)
├── Guaranteed delivery — packets are retried if lost
├── Ordered — packets arrive in the order sent
├── Slower — more overhead
└── Used for: HTTP, HTTPS, SSH, PostgreSQL, Redis, Kafka

UDP (User Datagram Protocol):
├── Connectionless — just fire packets and hope they arrive
├── No guarantee — packets can be lost, duplicated, reordered
├── Fast — minimal overhead
└── Used for: DNS queries, video streaming, games, Prometheus metrics (StatsD)
```

### The TCP Handshake (Know This!)

```
Client                     Server
  │                           │
  │──── SYN ────────────────► │   "I want to connect"
  │                           │
  │◄─── SYN-ACK ─────────── │   "OK, I acknowledge, and I'm ready"
  │                           │
  │──── ACK ────────────────► │   "Great, connection established"
  │                           │
  │══════ DATA FLOWS ══════════│
```

When you `telnet localhost 5432` and see "Connected", that handshake just happened.

---

## 🚪 PART 3: Ports — The Doors of a Server

A server can run hundreds of services, all sharing the same IP address. Ports (1-65535) differentiate them.

### Ports You MUST Memorize for This Stack:

| Port | Protocol | Service |
|------|----------|---------|
| 22 | TCP | SSH |
| 80 | TCP | HTTP (Nginx → Go) |
| 443 | TCP | HTTPS (Nginx TLS) |
| 5432 | TCP | PostgreSQL |
| 6379 | TCP | Redis |
| 6333 | TCP | Qdrant HTTP API |
| 6334 | TCP | Qdrant gRPC |
| 7233 | TCP | Temporal (gRPC) |
| 8080 | TCP | Pokevend Go API |
| 9092 | TCP | Kafka (client port) |
| 9090 | TCP | Prometheus metrics scrape |
| 11434 | TCP | Ollama AI API |

### Essential Port Commands:

```bash
# What's listening on what port?
ss -tlnp                    # Show TCP Listening ports with Process info
ss -tlnp | grep :5432       # Is Postgres listening?
ss -tlnp | grep :8080       # Is your Go app listening?

# Old version (use ss instead — ss is faster and more modern)
netstat -tlnp

# Who has a connection to what?
ss -tnp state ESTABLISHED   # All established connections

# Connect to a service to test it
telnet localhost 5432        # Can you reach Postgres? (Ctrl+] then quit)
nc -zv localhost 6379        # Can port 6379 be reached? (nc = netcat, -z = test only)
```

**HANDS-ON: POKEVEND NETWORK TROUBLESHOOTING (20 minutes)**

**Job Qualification**: *"Knowledge of platforms, infrastructure, or network troubleshooting techniques."*

When Pokevend is deployed, you'll use EXACTLY these commands to diagnose network problems:

```bash
# SCENARIO 1: Pokevend API won't start. Is port 8080 available?
echo "=== Checking if port 8080 is available ==="
ss -tlnp | grep :8080
# If nothing shows → port is free, problem is elsewhere
# If something shows → port is in use, kill that process first

# SCENARIO 2: The API is running but nginx can't reach it
echo ""
echo "=== Check if Go API is actually listening ==="
netstat -an | grep 8080 | grep LISTEN
# If nothing shows → API crashed or not listening
# If LISTEN shows → port is open, networking should work

# SCENARIO 3: Redis cache is supposed to be at port 6379 but not connecting
echo ""
echo "=== Can you connect to Redis? ==="
nc -zv localhost 6379 &>/dev/null && echo "Redis: REACHABLE" || echo "Redis: UNREACHABLE"
# REACHABLE = Redis running
# UNREACHABLE = Redis down or not on that port

# SCENARIO 4: Database connection pool is full. How many connections?
echo ""
echo "=== Current TCP connections (all states) ==="
ss -tnp state all | wc -l
# Compare against your max_connections setting in PostgreSQL
# If approaching limit → new connections will fail

# SCENARIO 5: Port scanning — what's the full listening surface?
echo ""
echo "=== ALL listening ports on this machine ==="
ss -tlnp | grep LISTEN
# This is what the firewall should control
```

---

## 🌐 PART 4: IP Addressing & Subnetting

### IPv4 Addresses

An IPv4 address is 4 numbers 0-255 separated by dots: `192.168.1.100`

Special ranges:
```
127.0.0.0/8    — Loopback (localhost) — traffic never leaves the machine
10.0.0.0/8     — Private (commonly used in corporate networks / VPCs)
172.16.0.0/12  — Private (Docker's default network range)
192.168.0.0/16 — Private (your home router)
```

### CIDR Notation — Subnet Masks

`10.0.0.0/16` means "the first 16 bits are the network, the rest are hosts"

```
10.0.0.0/8      — 16 million hosts (huge VPC)
10.0.0.0/16     — 65,536 hosts (large corporate subnet)
10.0.0.0/24     — 256 hosts (small team)
10.0.0.0/28     — 14 hosts (microservice subnet)
10.0.0.1/32     — A single specific IP
```

### Docker Networking Is Real Networking

When you run `docker-compose up`, Docker creates a virtual network:
```bash
docker network ls                           # List all docker networks
docker network inspect nexusos-network      # See IPs of all containers
docker exec nexusos-postgres ping nexusos-redis  # Can containers talk to each other?
```

Each container gets a private IP. Services discover each other by **name** (DNS):
```
# Inside docker-compose, "postgres" resolves to the postgres container's IP
# This is why your Go app connects to DB_HOST=postgres, not 192.168.x.x
DATABASE_URL=postgres://user:pass@postgres:5432/nexusos
```

**HANDS-ON: DOCKER CONTAINER NETWORKING (15 minutes)**

**Job Qualification**: *"Proficiency in scripting or programming to automate tasks, analyze data, and support infrastructure operations."*

When you deploy Pokevend in Docker, containers MUST talk to each other. This is how:

```bash
# STEP 1: Check what Docker networks exist RIGHT NOW
docker network ls
# You'll see: bridge, host, none (default Docker networks)
# When we deploy Pokevend, there will be a "nexusos-network" or similar

# STEP 2: Inspect a network (what containers are on it?)
docker network inspect bridge
# NOTICE: Each container has an IP address and a name
# The name is how INSIDE-DOCKER communication happens

# STEP 3: If Pokevend is running, check its network
# (We'll use this one your stack is deployed)
# docker network inspect nexusos-network
# You'll see entries for: postgres, redis, pokevend-api, etc.
# Each has: "Name": "container-name", "IPv4Address": "172.xx.x.xx"

# STEP 4: Test DNS inside a container
# When postgres container tries to reach redis, how does it know the IP?
# Ethe answer: Docker's built-in DNS resolver
# 
# Example (when Pokevend is running):
# docker exec nexusos-postgres nslookup redis
# Should return: Server: 127.0.0.11 (Docker DNS)
#               Address: <redis's IP>

# STEP 5: Network isolation test (CAN containers reach each other?)
# docker exec pokevend-api curl -I http://postgres:5432
# If this works → containers CAN communicate
# If timeout/refused → either container doesn't exist OR firewall blocks it
```

---

## 🔄 PART 5: DNS — The Phone Book of the Internet

**DNS (Domain Name System)** converts human names to IP addresses.

```
You type: pokevend.com
    ↓
Your computer asks: Local DNS cache
    ↓ (cache miss)
Asks: Your router (192.168.1.1)
    ↓ (doesn't know)
Asks: ISP's recursive resolver
    ↓
Asks: Root nameservers (.com)
    ↓
Asks: TLD nameservers (pokevend.com)
    ↓
Returns: 104.21.x.x
```

### DNS Record Types You Must Know:

```
A     — Maps hostname to IPv4: pokevend.com → 104.21.1.1
AAAA  — Maps hostname to IPv6
CNAME — Alias: www.pokevend.com → pokevend.com (then look up A)
MX    — Mail servers for a domain
TXT   — Text records (SPF, DKIM for email, domain verification)
NS    — Nameserver records (who manages this domain's DNS)
```

### DNS Commands:

```bash
dig pokevend.com             # Full DNS query (best tool)
dig pokevend.com A           # Only A records
dig @8.8.8.8 pokevend.com   # Use Google's DNS server specifically
nslookup pokevend.com        # Older alternative to dig
host pokevend.com            # Simple output

# Troubleshoot Docker DNS (is container name resolving correctly?)
docker exec nexusos-redis ping postgres  # Should resolve if on same network
```

**HANDS-ON: DNS DEBUGGING FOR POKEVEND (10 minutes)**

```bash
# When Pokevend starts, every service must find every other service by name
# If DNS fails → services can't talk → everything breaks

# TEST 1: Can you resolve names outside Docker?
dig google.com      # Should work (external DNS)
nslookup google.com # Alternative

# TEST 2: Local DNS resolution
dig localhost       # Should resolve to 127.0.0.1
dig $(hostname)     # What's your machine's DNS name?

# TEST 3: When Pokevend is running, check inter-service DNS
# (These will work when your stack is deployed)
# docker exec pokevend-api nslookup postgres
# docker exec pokevend-api nslookup redis
# docker exec pokevend-api nslookup kafka
# 
# What to expect:
# ✅ If it resolves → container can reach that service
# ❌ If "Name or service not known" → either:
#    - Service not running
#    - Service not on same Docker network
#    - Container name is different in docker-compose
```

---

## 🛡️ PART 6: Nginx as Reverse Proxy

A **reverse proxy** sits in front of your Go backend. It receives all internet traffic and forwards it internally. This is the standard production pattern.

```
Internet ──► Nginx (port 443) ──► Go API (port 8080)
                │
                ├── Handles TLS termination (HTTPS → HTTP internally)  
                ├── Load balancing (distributes across multiple Go instances)
                ├── Rate limiting at the HTTP layer
                ├── Compression (gzip)
                └── Static file serving
```

### Basic Nginx Config for Pokevend:

```nginx
# /etc/nginx/sites-available/pokevend

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name pokevend.com www.pokevend.com;
    return 301 https://$host$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name pokevend.com;

    # TLS certificates (from Let's Encrypt or self-signed)
    ssl_certificate     /etc/ssl/certs/pokevend.crt;
    ssl_certificate_key /etc/ssl/private/pokevend.key;
    
    # Only allow modern TLS (disable old, broken versions)
    ssl_protocols TLSv1.2 TLSv1.3;

    # Rate limiting: max 10 requests/second per IP (burst of 20)
    limit_req zone=api burst=20 nodelay;

    location /api/ {
        proxy_pass         http://localhost:8080;     # Forward to Go
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;   # Real client IP
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

---

## 🩺 PART 7: Network Troubleshooting Methodology

When something can't connect, follow this exact order:

```bash
# Step 1: Is the machine itself up?
ping 192.168.1.100          # Basic ICMP reachability

# Step 2: Is the port open?
nc -zv 192.168.1.100 5432   # TCP connection test to port 5432
# If this fails → firewall or service is not listening

# Step 3: Is the service listening?
ss -tlnp | grep :5432       # Is postgres bound to the port?
# If not listening → service is crashed or configured to wrong port

# Step 4: Is a firewall blocking it?
sudo iptables -L -n         # List all firewall rules
sudo ufw status verbose     # UFW firewall status

# Step 5: Is DNS working?
dig postgres                # Inside Docker container — should resolve
nslookup db.internal        # Custom DNS resolution

# Step 6: Is the APPLICATION responding correctly?
curl -v http://localhost:8080/health  # -v shows full HTTP headers
curl -k https://localhost/health      # -k = skip TLS verification

# Step 7: What do the logs say?
journalctl -u pokevend -n 50 --no-pager
docker logs nexusos-postgres --tail 50
```

---

## 📋 PRE-REQUISITES FOR WEEK 3

```bash
# Required tools
command -v ss nc dig curl ping traceroute

# Check docker network is healthy
docker network inspect nexusos-network

# Check all services are actually listening on their ports
ss -tlnp | grep -E ':5432|:6379|:8080|:6333'
```

---

## 🔗 Resources

- **Networking fundamentals**: https://www.cloudflare.com/learning/network-layer/what-is-the-network-layer/
- **How DNS works (visual)**: https://howdns.works/
- **Nginx docs**: https://nginx.org/en/docs/
- **Subnetting practice**: https://www.subnettingpractice.com/
- **Wireshark (packet capture tool)**: https://www.wireshark.org/
