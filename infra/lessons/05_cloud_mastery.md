# 📚 LESSON 05: Cloud Platforms, Observability & Troubleshooting
## MASTER REFERENCE — Read before touching any Week 5 scripts

---

## 🧠 The Mental Model: Cloud Is Programmable Infrastructure

The cloud is not magic. It is **the same Linux servers, networks, and storage you've been learning** — except they live in Amazon's or Microsoft's data center, and instead of physically racking them up, you provision them via API calls.

This is both the power and the complexity. You can spin up 100 servers in 30 seconds, and you can spin them down just as fast. This is only possible if your infrastructure is **fully automated and code-driven** (Infrastructure as Code).

---

## ☁️ PART 1: AWS Core Concepts

### The Big Picture — What AWS Gives You

```
┌────────────────────── AWS Account ──────────────────────────┐
│                                                              │
│  ┌──────────────────── VPC (Virtual Private Cloud) ───────┐ │
│  │  Your private network with your own IP range           │ │
│  │                                                        │ │
│  │  ┌─────────────────────────────────────────────────┐   │ │
│  │  │  Availability Zone A (us-east-1a)               │   │ │
│  │  │  ┌─────────────┐      ┌────────────────────┐    │   │ │
│  │  │  │Public Subnet│      │  Private Subnet    │    │   │ │
│  │  │  │(Load Bal.)  │─────►│  (Go API Servers)  │    │   │ │
│  │  │  └─────────────┘      └────────────────────┘    │   │ │
│  │  └─────────────────────────────────────────────────┘   │ │
│  │                                                        │ │  
│  │  ┌─────────────────────────────────────────────────┐   │ │
│  │  │  Availability Zone B (us-east-1b)               │   │ │
│  │  │  ┌─────────────┐      ┌────────────────────┐    │   │ │
│  │  │  │    ALB      │      │  Private Subnet    │    │   │ │  
│  │  │  │  (standby)  │─────►│  (Go API Servers)  │    │   │ │
│  │  │  └─────────────┘      └────────────────────┘    │   │ │
│  │  └─────────────────────────────────────────────────┘   │ │
│  │                                                        │ │
│  │  ┌──────────────────────── Isolated Subnet ──────────┐ │ │
│  │  │  RDS PostgreSQL (Multi-AZ Replica)                │ │ │
│  │  │  Cannot be reached from the internet AT ALL       │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Key AWS Services for Your Project

| Service | What It Is | For Pokevend |
|---------|------------|--------------|
| **EC2** | Virtual machines (Linux servers) | Run your Go backend |
| **RDS** | Managed PostgreSQL | Your database (automated backups, Multi-AZ) |
| **ElastiCache** | Managed Redis | Your Redis cache |
| **ALB** | Application Load Balancer | Distribute traffic across Go instances |
| **S3** | Object storage | Store DB backups, static files |
| **VPC** | Virtual network | Isolate your entire stack |
| **IAM** | Access management | Who can access what AWS resource |
| **CloudWatch** | Monitoring & logging | See your server metrics |
| **Route53** | DNS management | pokevend.com → ALB |
| **ACM** | TLS cert management | Free HTTPS certs |
| **Auto Scaling** | Automated horizontal scaling | More Go servers when traffic spikes |

---

## 🏗️ PART 2: Terraform — Infrastructure as Code

Terraform is the tool for defining cloud infrastructure as code. Instead of clicking through the AWS console, you write `.tf` files.

### Why Terraform Over Clicking AWS Console:

```
Console Clicking:         Terraform:
❌ Not reproducible       ✅ Run same config 100 times = same result
❌ Mistakes can't be      ✅ Version-controlled in Git
   tracked in Git         ✅ Diff changes before applying
❌ Hard to review         ✅ Team can review changes in PRs
❌ Can't automate         ✅ Runs in CI/CD pipelines automatically
```

### Terraform Core Commands:

```bash
terraform init      # Download provider plugins (like go mod download)
terraform plan      # SHOW what changes will be made (NO actual changes)
terraform apply     # APPLY the changes (actually builds infrastructure)
terraform destroy   # Tear EVERYTHING down
terraform state     # Inspect the state of existing infrastructure
```

### Terraform Resource Example:

```hcl
# main.tf

# Configure the AWS provider
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # Store state in S3 (prevents multiple engineers from stomping on each other)
  backend "s3" {
    bucket = "pokevend-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = "us-east-1"
}

# Variables (like function parameters)
variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "staging"
}

# A VPC (your private network)
resource "aws_vpc" "pokevend" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  
  tags = {
    Name        = "pokevend-vpc"
    Environment = var.environment
  }
}

# A subnet within the VPC
resource "aws_subnet" "private_api" {
  vpc_id            = aws_vpc.pokevend.id  # Reference another resource
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  
  tags = { Name = "pokevend-private-api-a" }
}

# An EC2 instance (your Go server)
resource "aws_instance" "pokevend_api" {
  ami           = "ami-0c02fb55956c7d316"  # Amazon Linux 2023
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.private_api.id
  
  user_data = <<-EOF
    #!/bin/bash
```

**HANDS-ON: DESIGN POKEVEND AWS INFRASTRUCTURE (20 minutes)**

**Job Qualification**: *"Exposure to cloud platforms (e.g. AWS, Azure) and understanding of hybrid infrastructure models."*

You're going to think through EVERY AWS component Pokevend needs:

```bash
# EXERCISE 1: Map Pokevend's deployment to AWS services
echo "=== POKEVEND → AWS MAPPING ==="
cat <<'EOF'
What we have locally:
├── docker-compose.yml (orchestrates containers)
├── postgres (database)
├── redis (cache)
├── go backend (API server)
└── Nginx (reverse proxy)

Maps to AWS:
├── ECS or EC2 (run containers or just the Go binary)
├── RDS PostgreSQL (managed database)
├── ElastiCache Redis (managed cache)
├── EC2 (run Go backend)
└── ALB/NLB (managed load balancer)

Why managed services?
- RDS = automated backups, Multi-AZ replicas, failover
- ElastiCache = no ops, automatic failover
- ALB = load balancing across multiple Go servers
EOF

# EXERCISE 2: Network design (security through architecture)
echo ""
echo "=== POKEVEND NETWORK TOPOLOGY IN AWS ==="
cat <<'EOF'
Your ideal production setup:

Internet
  │
  └──► ALB (public subnet, ports 80/443)
         │
         ├──► Go API instances (private subnet, port 8080 — NOT exposed to internet)
         │
         └──► PostgreSQL (RDS, even more private — only accessible from Go)

This means:
- Only the ALB is exposed to the internet
- Go API is NEVER directly reachable from outside
- Database is ONLY reachable from Go instances
- Auto Scaling: when load increases, launch more Go instances behind ALB
EOF

# EXERCISE 3: Calculate costs (important for business decisions!)
echo ""
echo "=== ROUGH AWS MONTHLY COST FOR POKEVEND ==="
cat <<'EOF'
Assume: moderate traffic (10,000 requests/day)

EC2:
  - 2x t3.medium (Go backend): 2 servers × $0.0416/hour × 730 hours = ~$60/month

RDS PostgreSQL:
  - db.t3.micro (managed): ~$25/month
  - 20GB storage: ~$2/month

ElastiCache Redis:
  - cache.t3.micro (managed): ~$20/month

ALB:
  - Fixed cost: $16/month
  - Requests: ~$0.0035 per million, so 300M/month = ~$1

Data Transfer:
  - Outbound traffic: ~$0.09/GB

TOTAL: ~$125-150/month (depending on traffic)

If you used RDS Multi-AZ (recommended for production):
  - Add another ~$25/month for standby replica
EOF

# EXERCISE 4: Ask yourself security questions
echo ""
echo "=== SECURITY DESIGN FOR POKEVEND AWS ==="
cat <<'EOF'
Q: Is the database publicly accessible? 
   A: NO. RDS should be in a private subnet with only Go instances allowed.

Q: Can someone directly SSH into my database server?
   A: NO. Databases are managed by AWS — you don't SSH into them.

Q: What if my Go instance is compromised?
   A: All they get is one t3.medium EC2 instance. Other instances continue running.
      ASG will auto-replace the compromised one.

Q: What if someone finds a password in the code?
   A: Use AWS Secrets Manager or Parameter Store — secrets are never in source.
      Go app retrieves secrets at startup from AWS.

Q: Do I need to manage OS patches?
   A: For EC2: yes, you need to update the AMI/instances
      For RDS: no, AWS handles patching automatically
   
   This is why managed services are valuable — less operational work.
EOF

```
    # This script runs when the instance FIRST boots
    # This is where you provision the server (run your 01_system_setup.sh!)
    sudo yum update -y
    curl -o /tmp/setup.sh https://s3.amazonaws.com/pokevend-deploy/setup.sh
    sudo bash /tmp/setup.sh
  EOF
  
  tags = { Name = "pokevend-api-server" }
}

# Output useful values after apply
output "api_private_ip" {
  value = aws_instance.pokevend_api.private_ip
}
```

---

## 📊 PART 3: Observability — You Cannot Fix What You Cannot See

### The Three Pillars of Observability

```
METRICS          — Numbers that describe the state of your system over time
                   "Go API processed 1450 requests in the last minute"
                   "PostgreSQL has 45 connections open"
                   Tool: Prometheus + Grafana

LOGS             — Timestamped records of discrete events
                   "2026-04-01T14:23:01 ERROR failed to connect to Redis: timeout"
                   Tool: Structured logging (slog) → Loki or ELK stack

TRACES           — The journey of a single request through multiple services
                   "This HTTP request took 230ms: 10ms Nginx, 5ms Go, 210ms DB query"
                   Tool: OpenTelemetry
```

### Prometheus — The Metrics Standard

Prometheus works by **scraping** metrics endpoints. Your Go app exposes `/metrics`, Prometheus polls it every 15 seconds.

```go
// In your Go backend — adding Prometheus metrics
import "github.com/prometheus/client_golang/prometheus"

// Define metrics
var (
    // Counter: only goes up (total requests ever)
    httpRequestsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "pokevend_http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "path", "status"},  // Labels = dimensions
    )
    
    // Histogram: distribution of values (request latency)
    httpRequestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "pokevend_http_request_duration_seconds",
            Help:    "HTTP request latency",
            Buckets: []float64{.005, .01, .025, .05, .1, .25, .5, 1, 2.5},
```

**HANDS-ON: MONITORING POKEVEND (20 minutes)**

**Job Qualification**: *"Design and implement scalable, reliable solutions to improve the efficiency and risk profile of technical platform."* — You cannot improve what you don't measure.

You're going to build monitoring questions you'll answer with metrics:

```bash
# METRICS PLANNING FOR POKEVEND
# "What does success look like?"

echo "=== CRITICAL POKEVEND METRICS ==="
cat <<'EOF'
GOLDEN SIGNALS (what you measure for every service):

1. LATENCY — How fast are requests?
   Question: Are card searches completing in < 500ms?
   Metric: pokevend_http_request_duration_seconds (percentiles: p50, p95, p99)
   Alert: If p99 latency > 1 second, page on-call engineer

2. TRAFFIC — How much load?
   Question: Are we hitting our rate limit?
   Metric: pokevend_http_requests_total (rate over time)
   Alert: If requests > 1000/sec, consider scaling

3. ERRORS — What's failing?
   Question: Are more than 0.5% of requests returning 5xx?
   Metric: pokevend_http_requests_total{status="5xx"} / pokevend_http_requests_total
   Alert: If error rate > 1%, page on-call engineer

4. SATURATION — Are we running out of resources?
   Question: Is the database running out of connections?
   Metric: pokevend_db_connections_active / pokevend_db_connections_max
   Alert: If connection pool > 80% full, investigate query slowness
EOF

# SETUP: Prometheus can be run as a container during dev
echo ""
echo "=== RUNNING PROMETHEUS LOCALLY (for testing) ==="
cat <<'EOF'
Create a scraape config:

# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'pokevend'
    static_configs:
      - targets: ['localhost:8080']  # Your Go API /metrics endpoint

Then run:
  docker run -d -p 9090:9090 -v \$(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus

Access Prometheus UI at: http://localhost:9090
Query examples:
  - rate(pokevend_http_requests_total[5m])  # Requests per second
  - histogram_quantile(0.99, pokevend_http_request_duration_seconds)  # p99 latency
  - pokevend_db_connections_active  # Current DB connections
EOF

# PRACTICE: What would these PromQL queries tell you?
echo ""
echo "=== PRACTICE: INTERPRET THESE PROMETHEUS QUERIES ==="
cat <<'EOF'
Q: What does this query MEAN?
   rate(pokevend_http_requests_total{status="500"}[5m])
A: "HTTP 500 errors per second, averaged over the last 5 minutes"
   → Use this to trigger alerts when error rate spikes

Q: What does this query MEAN?
   histogram_quantile(0.95, rate(pokevend_http_request_duration_seconds_bucket[5m]))
A: "The latency that 95% of users experience (5th percentile is bad)"
   → If this is > 1 second, 1 in 20 users have slow requests

Q: What does this query MEAN?
   pokevend_db_connections_active / pokevend_db_connections_max
A: "Current database connection pool utilization"
   → At 100%, new queries will be rejected, causing errors
EOF

# ALERT DESIGN: What should trigger a page?
echo ""
echo "=== POKEVEND ALERTING RULES ==="
cat <<'EOF'
Alert Rule 1: High Error Rate
  Condition: error_rate > 1% for 2 minutes
  Action: Page on-call engineer
  Why: Users are getting errors — immediate action needed

Alert Rule 2: P99 Latency High
  Condition: p99_latency > 1 second for 5 minutes
  Action: Page on-call engineer
  Why: User experience is degrading — need to investigate

Alert Rule 3: Database Connection Pool Exhausted
  Condition: active_connections > max_connections * 0.9
  Action: Page on-call engineer
  Why: New requests will fail — need to scale or fix slow queries

Alert Rule 4: Out of Disk Space
  Condition: disk_usage > 90%
  Action: Alert (not page, but critical)
  Why: Logs will be dropped, database will fail — need cleanup/scale

Alert Rule 5: Service Down
  Condition: no heartbeat for 60 seconds
  Action: Page immediately
  Why: Service is completely dead
EOF

```
        },
        []string{"method", "path"},
    )
    
    // Gauge: can go up and down (current connections)
    activeConnections = prometheus.NewGauge(prometheus.GaugeOpts{
        Name: "pokevend_active_connections",
        Help: "Number of active database connections",
    })
)
```

### Grafana Dashboard — Visualizing Metrics

Grafana queries Prometheus and draws graphs. Key panels for Pokevend:

```
Panel 1: Request Rate
  Query: rate(pokevend_http_requests_total[5m])
  Shows: How many requests per second right now?

Panel 2: Error Rate (RED Method)
  Query: rate(pokevend_http_requests_total{status=~"5.."}[5m]) 
          / rate(pokevend_http_requests_total[5m])
  Shows: What % of requests are failing?

Panel 3: Latency (p50, p99)
  Query: histogram_quantile(0.99, rate(pokevend_http_request_duration_seconds_bucket[5m]))
  Shows: The WORST 1% of your users' latency

Panel 4: Database Connection Pool
  Query: pokevend_db_connections_active
  Shows: Are you running out of DB connections?
```

### The USE Method — Troubleshooting Framework

For EVERY resource (CPU, memory, disk, network), ask:
- **U**tilization — How busy is it? (CPU at 80%)
- **S**aturation — Is it overloaded? (Job queue is growing)
- **E**rrors — Are there errors? (Disk I/O errors)

```bash
# CPU: Utilization + Saturation
top                         # Overall CPU %
cat /proc/loadavg           # Load avg (1, 5, 15 min). Divide by CPU count.
                            # Load avg > 1.0 per CPU = saturation!

# Memory: Utilization
free -h                     # Total, Used, Available
cat /proc/meminfo           # Detailed breakdown

# Disk: Utilization + Errors
df -h                       # Disk space % used
iostat -x 1                 # Disk I/O utilization (install: sudo apt install sysstat)
                            # %util > 90% = disk is saturated

# Network: Errors
ip -s link                  # Network interface stats including errors/drops
ss -s                       # Socket summary statistics
```

---

## 🔥 PART 4: Incident Response

### When Production Goes Down — The Process

```
1. DETECT    → Monitoring alert fires (Prometheus → Grafana → PagerDuty)
2. TRIAGE    → How bad is it? All users? Some users? One region?
3. MITIGATE  → Restore service first (rollback, restart, scale up)
               DO NOT try to fix the root cause while users are affected
4. DIAGNOSE  → Now find the root cause with logs, metrics, traces
5. FIX       → Apply the real fix
6. VALIDATE  → Confirm the fix worked via monitoring
7. DOCUMENT  → Write an Incident Report (RCA — Root Cause Analysis)
```

### The Incident Report Template

```markdown
# Incident Report: [Service] [Date]
**Severity**: P1 (Complete Outage) / P2 (Degraded) / P3 (Minor)
**Duration**: 14:32 UTC – 15:45 UTC (73 minutes)
**Impact**: All Pokevend API users could not search cards

## Timeline
- 14:32 — Monitoring alerts fire: API error rate > 10%
- 14:35 — Engineer paged
- 14:42 — Identified: PostgreSQL connection pool exhausted
- 14:50 — Mitigated: Restarted API service to release connections
- 15:20 — Root cause found: slow query causing connection pile-up
- 15:45 — Fix deployed: query index added, verified by monitoring

## Root Cause
A missing index on the `cards.set_name` column caused a full table scan on
every GetBySetName call. With high traffic, these slow queries held connections
open for 30+ seconds, exhausting the pool (max 25 connections).

## What Went Wrong
- No database query performance monitoring
- Index was missed during code review

## Action Items
- [ ] Add `pg_stat_activity` monitoring to Grafana dashboard
- [ ] Add slow query threshold alert (> 1 second = alert)
- [ ] Review all table scans in production query logs
```

---

## 📋 PRE-REQUISITES FOR WEEK 5

```bash
# Terraform
terraform version           # Should exist

# AWS CLI (optional — for actually provisioning)
aws --version
aws configure               # Set up your credentials

# Monitoring tools
docker pull prom/prometheus
docker pull grafana/grafana
```

---

## 🔗 Resources

- **Terraform on AWS**: https://developer.hashicorp.com/terraform/tutorials/aws-get-started
- **Prometheus docs**: https://prometheus.io/docs/introduction/overview/
- **Grafana**: https://grafana.com/docs/grafana/latest/
- **AWS Free Tier**: https://aws.amazon.com/free/ — $0 to experiment
- **The Google SRE Book**: https://sre.google/sre-book/table-of-contents/ — Free, industry bible
- **USE Method**: https://www.brendangregg.com/usemethod.html
