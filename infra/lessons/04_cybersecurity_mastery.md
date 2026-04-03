# 📚 LESSON 04: Cybersecurity — Zero Trust Architecture
## MASTER REFERENCE — Read before touching any Week 4 scripts

---

## 🧠 The Mental Model: Assume the Breach

The old security model was "build a wall, trust everything inside it." This is called **Castle-and-Moat** security, and it has been dead since 2000.

The new model is **Zero Trust**:
> "Never trust, always verify. Every identity must authenticate, every request must be authorized, regardless of where it comes from — even from inside your own network."

This matters because:
- Employees get phished → attacker is now "inside the castle"
- A container gets compromised → attacker can reach other containers on the same Docker network
- A developer commits a secret to Git → that secret is now public forever

Your job is to design a system where even if one component is compromised, the **blast radius** (how far the damage spreads) is as small as possible.

---

## 🔐 PART 1: Access Controls — Who Can Touch What

### Three Questions for Every Resource:
1. **Authentication**: Who are you? (Prove your identity)
2. **Authorization**: Are you allowed? (Do you have permission)
3. **Accounting**: What did you do? (Log everything)

### The Database — Least Privilege in Practice

This is the Pokevend PostgreSQL schema approach. Most developers create one superuser DB account and use it everywhere. This is catastrophic.

```sql
-- BAD: One user with full power
CREATE USER app WITH PASSWORD 'pass123';
GRANT ALL PRIVILEGES ON DATABASE pokevend TO app;

-- GOOD: Separate roles with minimal permissions
-- The API can only read/write specific tables
CREATE ROLE pokevend_api WITH LOGIN PASSWORD 'strong-random-password';
GRANT CONNECT ON DATABASE pokevend TO pokevend_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON cards, users, price_history TO pokevend_api;
-- The API CANNOT: DROP tables, CREATE tables, access other databases

-- A read-only role for analytics/reporting
CREATE ROLE pokevend_readonly WITH LOGIN PASSWORD 'another-strong-password';
GRANT CONNECT ON DATABASE pokevend TO pokevend_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO pokevend_readonly;
-- This user can ONLY read. Impossible to corrupt data.

-- A migration role (only used by CI/CD pipeline)
CREATE ROLE pokevend_migrate WITH LOGIN PASSWORD 'migration-password';
GRANT pokevend_api TO pokevend_migrate;
GRANT CREATE ON SCHEMA public TO pokevend_migrate; -- Can create/alter tables
```

### Linux User Permissions Revisited

```bash
# The Pokevend service account strategy
sudo useradd --system --no-create-home --shell /bin/false pokevend-svc

# Its binary and config: owned by root (it CAN'T modify its own binary)
sudo chown root:root /opt/pokevend/pokevend
sudo chmod 755 /opt/pokevend/pokevend

# Its log directory: owned by it (CAN write logs)
sudo chown pokevend-svc:pokevend-svc /var/log/pokevend
sudo chmod 750 /var/log/pokevend

# Its config (secrets): owned by root, readable by service group only
sudo chown root:pokevend-svc /etc/pokevend/config.env
sudo chmod 640 /etc/pokevend/config.env   # rw-r----- (owner rw, group r, others nothing)
```

---

## 🔑 PART 2: Secrets Management — Never Hardcode Credentials

### The OWASP Top 10 includes "Cryptographic Failures" — This Is It

What NOT to do (this gets you fired or hacked):
```bash
# In your Go code — NEVER do this
db := sql.Open("postgres", "postgres://admin:superpassword@localhost/pokevend")

# In your .env committed to Git — fires you immediately
DB_PASSWORD=superpassword123
JWT_SECRET=mysecretkey
```

What TO do:
```bash
# .env is in .gitignore — never committed
echo ".env" >> .gitignore

# Use environment variables that the systemd service injects
# /etc/pokevend/config.env (only readable by pokevend-svc group)
DB_PASSWORD=<randomly-generated-64-char-string>
JWT_SECRET=<randomly-generated-64-char-string>

# Generate secrets properly in bash
openssl rand -base64 64 | tr -d '\n'    # 64-byte base64-encoded random string
python3 -c "import secrets; print(secrets.token_hex(32))"  # 32-byte hex string
```

### Secrets Audit — Finding Exposed Credentials

```bash
# Search your repo for accidentally committed secrets
git log --all -p | grep -i "password\|secret\|key\|token" | grep "^+" | grep -v "^+#"

# Search for common patterns (API keys, DB URLs, etc.)
grep -rn "password\s*=" ./ --include="*.go" --include="*.py" --include="*.env"
grep -rn "sk-[a-zA-Z0-9]" ./   # OpenAI API key pattern
grep -rn "AKIA[A-Z0-9]" ./     # AWS Access Key pattern

# Use git-secrets tool to prevent accidental commits
# Install: sudo apt install git-secrets
# Setup: git secrets --install && git secrets --register-aws```

**HANDS-ON: AUDIT POKEVEND REPO FOR LEAKED SECRETS (15 minutes)**

**Job Qualification**: *"Understanding of basic cybersecurity principles, including access controls, segmentation, and secure configuration practices."*

You're going to scan YOUR actual project files for accidentally exposed secrets:

```bash
# TEST 1: Do any .env files exist and are they in .gitignore?
echo "=== Check .env security ==="
ls -la shopify/.env* 2>/dev/null || echo "No .env files found (good!)"
grep "\.env" shopify/.gitignore 2>/dev/null && echo ".env is ignored (good!)" || echo "WARNING: .env might be committed!"

# TEST 2: Scan for password patterns in Go code
echo ""
echo "=== Scanning for hardcoded passwords in Go ==="
grep -r "password" shopify/Pokemon/server/ --include="*.go" 2>/dev/null | grep -v "TODO\|schema" | head -5

# TEST 3: Scan for API keys in Python code
echo ""
echo "=== Scanning for API keys in Python ==="
grep -r "OPENAI\|STRIPE\|AWS_SECRET" shopify/services/ai/ --include="*.py" 2>/dev/null | head -5

# TEST 4: Check git history for secrets (did you accidentally commit one?)
echo ""
echo "=== Checking git history for password commits ==="
cd shopify
git log --all -p --diff-filter=M | grep -i "password\|secret" | head -3 || echo "No obvious secrets in git history"
cd ..

# TEST 5: Find config files that might have secrets
echo ""
echo "=== Finding potentially sensitive config files ==="
find shopify -name "*.env" -o -name "*.conf" -o -name "*secret*" 2>/dev/null | head -10

# TEST 6: Check for .env.example (this is OK — it's a template)
echo ""
echo "=== Template files (these are OK to commit) ==="
find shopify -name ".env.example" -o -name "*.example" 2>/dev/null
# These show structure WITHOUT real credentials```

---

## 🔥 PART 3: Firewalls — The Network Gates

### UFW (Uncomplicated Firewall) — Your Main Tool

UFW is a frontend for `iptables` (which is the actual Linux kernel firewall). UFW makes it human-readable.

```bash
# The philosophy: Default DENY everything, then whitelist only what's needed
sudo ufw default deny incoming          # Block all incoming traffic by default
sudo ufw default allow outgoing         # Allow all outgoing (your server can call out)

# Allow specific ports
sudo ufw allow 22/tcp                   # SSH
sudo ufw allow from 10.0.0.0/8 to any port 22   # SSH only from private network
sudo ufw allow 80/tcp                   # HTTP
sudo ufw allow 443/tcp                  # HTTPS

# Block specific IP (Fail2Ban does this automatically)
sudo ufw deny from 1.2.3.4 to any

# Application profiles (UFW knows about common apps)
sudo ufw allow 'Nginx Full'             # Allows both 80 and 443

sudo ufw enable                         # TURN IT ON (do this LAST)
sudo ufw status verbose                 # Show all rules
sudo ufw status numbered                # Show rules with numbers (for deletion)
sudo ufw delete 3                       # Delete rule #3
```

**HANDS-ON: POKEVEND FIREWALL SECURITY PLANNING (15 minutes)**

**Job Qualification**: *"Familiarity with infrastructure protocols and configurations, as well as security tools such as firewalls, antivirus software, intrusion detection/prevention systems (IDS/IPS), and endpoint protection platforms."*

You're going to design a firewall for Pokevend that ONLY exposes what's needed:

```bash
# ANALYSIS: What ports does Pokevend NEED to listen on?
echo "=== POKEVEND PORT REQUIREMENTS ==="
echo "Port 22:   SSH (for admin access)"
echo "Port 80:   HTTP (Nginx receives requests)"
echo "Port 443:  HTTPS (Nginx TLS)"
echo "Port 8080: Go API (internal only — NOT exposed to internet)"
echo "Port 5432: PostgreSQL (internal only — NOT exposed to internet)"
echo "Port 6379: Redis (internal only)"
echo ""
echo "SECURITY RULE: Ports 8080, 5432, 6379 should ONLY be accessible"
echo "from within the Docker network, NOT from the internet"

# DESIGN: What UFW rules would you create?
echo ""
echo "=== PROPOSED UFW RULES FOR POKEVEND ==="
cat <<'EOF'
# Allow SSH from anywhere (or restrict to your office IP)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS from anywhere (the internet accesses Nginx)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# DENY Go API from outside (it's behind Nginx)
sudo ufw deny 8080/tcp

# DENY database from outside (it's inside Docker)
sudo ufw deny 5432/tcp
sudo ufw deny 6379/tcp

# Enable the firewall
sudo ufw enable

# Verify
sudo ufw status verbose
EOF

# CURRENT STATE: Check what UFW is doing NOW
echo ""
echo "=== CURRENT FIREWALL STATE ==="
sudo ufw status verbose 2>/dev/null || echo "UFW not yet enabled"

# TESTING: Test connectivity to each port (when Pokevend is running)
echo ""
echo "=== PORT CONNECTIVITY TESTS (when Pokevend deployed) ==="
cat <<'EOF'
# Test HTTP
curl -I http://localhost:80

# Test HTTPS (will fail self-signed cert, but connection should work)
curl -I -k https://localhost:443

# Test API (should fail if not exposed)
curl -I http://localhost:8080 || echo "✓ Port 8080 correctly blocked"

# Test database
nc -zv localhost 5432 2>&1 | grep -i "refused\|refused" && echo "✓ Port 5432 correctly blocked"
EOF

```

### iptables — The Underlying Engine

UFW generates iptables rules. Understanding iptables lets you handle complex scenarios.

```bash
# List current rules
sudo iptables -L -n -v                  # All chains, verbose

# The three default chains:
# INPUT   — traffic coming TO this machine
# OUTPUT  — traffic leaving FROM this machine
# FORWARD — traffic passing THROUGH this machine (router/proxy)

# Block a specific IP from reaching port 5432 (PostgreSQL)
sudo iptables -A INPUT -s 192.168.1.100 -p tcp --dport 5432 -j DROP

# Allow established connections (critical — otherwise you block your own replies!)
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
```

---

## 🕵️ PART 4: IDS/IPS — Intrusion Detection & Prevention

### The Difference:
- **IDS (Detection)**: Watches for attacks, alerts you, does nothing
- **IPS (Prevention)**: Watches for attacks and actively BLOCKS them

### Fail2Ban — The Practical IPS for Linux

Fail2Ban scans log files for patterns (too many failed logins), then automatically adds `iptables` block rules.

```bash
# How it works:
# 1. You define "jails" (monitoring rules) in /etc/fail2ban/jail.local
# 2. Each jail watches a log file for a pattern
# 3. If pattern matches X times in Y seconds, ban the IP for Z minutes

# /etc/fail2ban/jail.local
[DEFAULT]
bantime  = 1h           # Ban for 1 hour
findtime = 10m          # Look for failures within 10 minutes
maxretry = 5            # 5 failures in findtime = banned

[sshd]
enabled = true
port    = ssh
filter  = sshd
logpath = /var/log/auth.log
maxretry = 3            # SSH: only 3 tries (stricter)

[pokevend-api]
enabled  = true
port     = http,https
filter   = pokevend-api          # Uses our custom filter below
logpath  = /var/log/nginx/access.log
maxretry = 20                    # Block after 20 failed auth attempts in 10min
bantime  = 24h                   # API brute force: ban for 24 hours

# /etc/fail2ban/filter.d/pokevend-api.conf
[Definition]
failregex = ^<HOST> .* "(POST|GET) /api/v1/auth/(login|register).*" 401
ignoreregex =
```

```bash
# Fail2Ban commands
sudo fail2ban-client status           # All jails
sudo fail2ban-client status sshd      # Specific jail — how many IPs banned
sudo fail2ban-client unban 1.2.3.4   # Unban an IP
sudo fail2ban-client banned          # List all currently banned IPs
```

---

## 🐳 PART 5: Docker Security — Containers Are Not a Sandbox

**Myths about Docker security:**
1. ❌ "Containers are isolated — what happens inside can't escape"
2. ❌ "Running as root in a container is fine, it's not REAL root"
3. ❌ "Docker networking is secure by default"

**Reality:**
1. Container users map to host users. A container running as root = root on the host if misconfigured
2. All containers on the same `docker-compose` network can talk to each other — including your database
3. Containers expose ports to the entire machine by default

### Docker Hardening Checklist:

```yaml
# docker-compose.yml hardening examples

services:
  pokevend-api:
    image: pokevend:latest
    
    # ⭐ NEVER run containers as root
    user: "1001:1001"       # Run as UID:GID 1001 (non-root)
    
    # Read-only filesystem — app can't modify its own container
    read_only: true
    
    # Mount writable dirs explicitly (only what's needed)
    tmpfs:
      - /tmp               # In-memory temp files
    
    # Drop ALL Linux capabilities, add only what's needed
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE   # Only if it needs to bind to ports < 1024
    
    # Prevent privilege escalation (e.g. setuid binaries)
    security_opt:
      - no-new-privileges:true
    
    # Resource limits (prevent a compromised container from consuming all CPU/RAM)
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 512M
    
    # Only expose what's needed
    expose:
      - "8080"            # Internal only — not published to host
    # NOT: ports: - "8080:8080" (that publishes to all interfaces)
```

### Docker Network Segmentation:

```yaml
# Instead of all services on one network, segment them:
networks:
  frontend:            # Nginx can reach this
    driver: bridge
  backend:             # Go API is here
    driver: bridge
  database:            # Only Go API and Postgres are here
    driver: bridge
    internal: true     # Cannot reach the internet at all

services:
  nginx:
    networks: [frontend, backend]
  pokevend-api:
    networks: [backend, database]
  postgres:
    networks: [database]   # Postgres CANNOT be reached from frontend!
```

---

## 🔍 PART 6: Vulnerability Scanning

### What to Scan For:

```bash
# ── Dependencies ──────────────────────────────────────────────────────────
# Python: check for packages with known CVEs
pip install pip-audit
pip-audit -r requirements.txt

# Go: check for vulnerable dependencies
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...

# JavaScript/Node
npm audit
npm audit fix

# ── Docker images ─────────────────────────────────────────────────────────
# Install Trivy (best free Docker scanner)
# sudo apt install trivy
trivy image pokevend:latest              # Scan your image for CVEs
trivy fs ./                             # Scan your filesystem

# ── Open ports (external perspective) ────────────────────────────────────
nmap -sV localhost                      # What services + versions are exposed?
nmap -p 1-10000 localhost               # Scan all ports 1-10000

# ── SSL/TLS configuration ─────────────────────────────────────────────────
# Install testssl.sh
# bash testssl.sh https://pokevend.com  # Check TLS config quality
```

---

## 📋 PRE-REQUISITES FOR WEEK 4

```bash
# Check these tools exist
command -v ufw fail2ban-client openssl

# Review current firewall state
sudo ufw status

# Check for any world-readable sensitive files (REAL security audit)
find /etc/pokevend -maxdepth 2 -perm -004 2>/dev/null   # Other-readable files
find /opt/pokevend -maxdepth 2 -perm -002 2>/dev/null   # World-writable (dangerous)
```

---

## 🔗 Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/ — Read all 10
- **Fail2Ban docs**: https://www.fail2ban.org/wiki/index.php/MANUAL_0_8
- **Docker security best practices**: https://docs.docker.com/engine/security/
- **CIS Benchmarks**: https://www.cisecurity.org/cis-benchmarks — The gold standard for hardening guides
- **CVE database**: https://cve.mitre.org/ — Look up vulnerability IDs
