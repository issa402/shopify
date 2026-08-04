# 📚 LESSON 01: Linux Deep Dive & System Administration
## MASTER REFERENCE — Read this before touching any Week 1 scripts

---

## ⚡ The Mental Model That Changes Everything

Linux is not an app. Linux is a **kernel** — a piece of software that sits between your hardware (CPU, RAM, disk) and all other programs. Every time your Go backend touches a database, the kernel is mediating that. Every packet that comes in from the internet, the kernel decides where it goes.

**The kernel thinks in terms of:**
- **Processes** — running programs (your Go API = a process)
- **Files** — literally everything is a file (your network socket = a file, your disk = a file, your RAM = a file in `/proc`)
- **Users** — who is allowed to touch what

If you don't understand these three things, you cannot do infrastructure.

---

## 🗂️ PART 1: The Filesystem — Where Everything Lives

### The Linux Directory Hierarchy (Memorize This)

```
/                   ← Root. The top of everything.
├── bin/            ← Essential commands: ls, cat, cp (available before login)
├── etc/            ← ⭐ ALL system configuration lives here (nginx.conf, systemd services)
├── home/           ← User home directories (/home/iscjmz)
├── opt/            ← ⭐ Where you install apps (put your Go binary in /opt/pokevend/)
├── proc/           ← ⭐ VIRTUAL filesystem. The kernel exposes process info as files here
│   ├── meminfo     ← Current RAM usage (cat /proc/meminfo)
│   ├── cpuinfo     ← CPU info (cat /proc/cpuinfo)
│   ├── loadavg     ← System load (cat /proc/loadavg)
│   └── <PID>/      ← Every running process has a folder with its entire state
├── sys/            ← Another virtual filesystem. Kernel device/hardware info
├── tmp/            ← Temporary files. Wiped on reboot.
├── usr/            ← User programs and libraries
│   └── local/bin/  ← Where YOU put custom binaries (alternative to /opt)
├── var/            ← Variable data — things that CHANGE
│   ├── log/        ← ⭐ ALL logs live here (nginx, syslog, your app logs)
│   └── run/        ← PID files, socket files for running services
└── root/           ← Root user's home directory (NOT /home/root)
```

### Why This Matters for Pokevend:
- Your **Go binary** goes in `/opt/pokevend/pokevend`
- Your **logs** go in `/var/log/pokevend/app.log`
- Your **systemd service file** goes in `/etc/systemd/system/pokevend.service`
- Your **config file** goes in `/etc/pokevend/config.env`
- Your **DB backups** go in `/var/backups/pokevend/`

**HANDS-ON EXERCISE: Map Your System RIGHT NOW (10 mins)**

Execute these to build intuition about how Linux is organized:

```bash
# Where do apps live?
ls -la /opt/
ls -la /etc/ | head -20

# What's the kernel telling you?
cat /proc/loadavg          # Is system under load?
cat /proc/meminfo | head -5 # How much RAM is in use?

# This is POKEVEND's filesystem:
df -h | grep -E "Filesystem|/$|var"     # Disk usage
ls -la /var/log/           # This is where Pokevend logs will go
ls -la /opt/               # This is where the binary will live
```

**Critical Questions After Running:**
1. What does a load average of "2.5 1.8 0.9" mean on a 4-core CPU?
2. If `/var` is 92% full, what happens to logging?
3. Why would you put the database on a separate filesystem?

---

## 👤 PART 2: Users, Groups & Permissions — The Security Foundation

### The Permission Model

Every file in Linux has three things:
1. An **owner** (a user)
2. A **group** (a collection of users)
3. **Permission bits** (who can do what)

```bash
$ ls -la /etc/passwd
-rw-r--r-- 1 root root 2847 Mar 25 10:00 /etc/passwd
│││ │││ │││
│││ │││ └── Others can: r (read)
│││ └────── Group can: r (read)  
└────────── Owner can: rw (read+write)

# Format: [type][owner perms][group perms][other perms]
# d = directory, - = file, l = symlink
```

### Permission Numbers (Octal — You WILL use these)

```
4 = read  (r)
2 = write (w)  
1 = execute (x)
0 = nothing

# Add them together:
7 = 4+2+1 = rwx (full access)
6 = 4+2   = rw- (read and write)
5 = 4+1   = r-x (read and execute)
4 = 4     = r-- (read only)
0 = 0     = --- (no access)

# chmod 750 myfile means:
# Owner: 7 = rwx
# Group: 5 = r-x
# Others: 0 = --- (no one else)
```

### The Principle of Least Privilege — THE Most Important Security Concept

> **RULE: Every process should have ONLY the permissions it needs to do its job. Nothing more.**

**DIRECTLY TIED TO JOB QUALIFICATION**: *"Understanding of basic cybersecurity principles, including access controls, segmentation, and secure configuration practices."*

Applied to Pokevend:
```bash
# ❌ BAD: Running Pokevend as root
# Exploit in the API code → attacker becomes root → they own everything

# ✅ GOOD: Dedicated, locked-down service user
sudo useradd \
  --system \          # System account (no home dir, can't login)
  --no-create-home \
  --shell /bin/false \ # Can't open a shell even if they try
  --comment "Pokevend Service Account" \
  pokevend-svc
```

**HANDS-ON: PROVE WHY THIS MATTERS (5 minutes)**

```bash
# 1. What CAN you (normal user) do?
echo "=== Normal User: $(whoami) ==="
id
cat /etc/shadow 2>&1 | head -1     # Try to read password hashes
systemctl restart nginx 2>&1 | head -1  # Try to restart services

# 2. What CAN root do?
echo ""
echo "=== Root ===" 
sudo id
sudo cat /etc/shadow | head -1     # Root CAN read password hashes
sudo systemctl restart nginx 2>&1 | head -1  # Root CAN restart services

# 3. If Pokevend is compromised (attacker gets pokevend-svc privs)
echo ""
echo "=== Compromised: running as pokevend-svc ==="
sudo -u nobody cat /etc/shadow 2>&1 | head -1    # Still denied!
sudo -u nobody systemctl restart nginx 2>&1      # Still denied!
```

**The Lesson**: When Pokevend runs as `pokevend-svc` with restrictive permissions, an attacker can only touch files Pokevend owns. They CAN'T read `/etc/shadow`, restart services, or access other apps' data. This **segmentation** is your defense.

### Key Commands (Practice All of These):

```bash
# User management
id                          # Who am I? What groups am I in?
who                         # Who else is logged in?
cat /etc/passwd             # All users on the system
cat /etc/shadow             # Password hashes (root only)
sudo useradd -r -s /bin/false myservice  # Create service user

# Permission management  
ls -la <file>               # See permissions
chmod 750 <file>            # Change permissions (owner=rwx, group=r-x, others=none)
chown user:group <file>     # Change owner and group
chown pokevend-svc:pokevend-svc /opt/pokevend/  # Give the dir to our service user

# Group management
groups                      # What groups am I in?
sudo usermod -aG docker iscjmz  # Add yourself to docker group
```

---

## ⚙️ PART 3: Processes & Systemd — Keeping Services Alive

### What is a Process?

When you run `./pokevend`, Linux creates a **Process** with:
- A **PID** (Process ID) — a unique number
- A **PPID** (Parent PID) — who spawned it
- An **owner** (what user it runs as)
- **File descriptors** (open files, including sockets)
- A **working directory**

```bash
# Viewing processes
ps aux                      # All processes, all users
ps aux | grep pokevend      # Find pokevend specifically
top                         # Live process monitor
htop                        # Better live monitor (install: sudo apt install htop)

# Killing processes
kill 1234                   # Send SIGTERM (graceful shutdown) to PID 1234
kill -9 1234                # Send SIGKILL (force kill — use as last resort)
pkill pokevend              # Kill by name

# Process hierarchy
pstree                      # See the whole process tree
```

### What is Systemd?

**Systemd** is the "init system" — the very first process that Linux starts (PID 1). Everything else is its child. It is responsible for:
1. Starting services when the machine boots
2. Restarting services if they crash
3. Collecting logs from services (via `journald`)
4. Managing dependencies between services

### Anatomy of a Systemd Service File

```ini
# /etc/systemd/system/pokevend.service

[Unit]
Description=Pokevend Card Market API        # Human name
After=network.target postgresql.service     # Don't start until THESE are running
Wants=postgresql.service                    # "Soft" dependency — want it, but don't require it
Requires=redis.service                      # "Hard" dependency — fail if redis isn't up

[Service]
Type=simple                 # Process stays in foreground (default for Go apps)
User=pokevend-svc           # ⭐ Run as this locked-down user (NOT root)
Group=pokevend-svc          
WorkingDirectory=/opt/pokevend   # The binary's CWD
ExecStart=/opt/pokevend/pokevend # The command to run
ExecReload=/bin/kill -HUP $MAINPID  # How to reload config without restarting

Restart=always              # ⭐ Restart if it crashes
RestartSec=5s               # Wait 5 seconds before restarting
StartLimitBurst=5           # If it fails 5 times in a row...
StartLimitInterval=30s      # ...within 30s, stop trying to restart

# Environment variables (NEVER put secrets here — use EnvironmentFile instead)
EnvironmentFile=/etc/pokevend/config.env  # Load env vars from this file

# Resource limits
LimitNOFILE=65536           # Max open files (important for high-concurrency servers)

# Logging
StandardOutput=journal      # Stdout goes to systemd journal
StandardError=journal       # Stderr too

[Install]
WantedBy=multi-user.target  # Start this service when the system reaches "normal" mode
```

### Systemd Commands (You'll Use These Daily):

```bash
# Managing services
sudo systemctl start pokevend       # Start it
sudo systemctl stop pokevend        # Stop it
sudo systemctl restart pokevend     # Stop then start
sudo systemctl reload pokevend      # Send SIGHUP (reload config without stopping)
sudo systemctl status pokevend      # ⭐ Is it running? What's the status?
sudo systemctl enable pokevend      # Start automatically on boot
sudo systemctl disable pokevend     # Don't start on boot

# After editing the .service file, you MUST reload:
sudo systemctl daemon-reload        # ⭐ Tell systemd to re-read all service files

# Logs (THIS IS HOW YOU DEBUG CRASHES)
sudo journalctl -u pokevend         # All logs for pokevend service
sudo journalctl -u pokevend -f      # Follow logs (like tail -f)
sudo journalctl -u pokevend --since "10 minutes ago"
sudo journalctl -u pokevend -n 50   # Last 50 lines
```

**HANDS-ON: UNDERSTAND SYSTEMD (15 minutes)**

**Job Qualification Alignment**: *"Proficiency in scripting or programming to automate tasks, analyze data, and support infrastructure operations."* — Systemd is HOW you automate service management.

```bash
# 1. What systemd services are currently running?
systemctl list-units --type=service --state=running | head -10

# 2. Check a specific service (e.g., Docker or nginx if installed)
systemctl status docker
# Notice: Active status, Restart count, Last heartbeat, Process ID (PID)

# 3. Look at systemd's view of the system
systemctl status --all
# This shows systemd's understanding of EVERYTHING running

# 4. See systemd's boot messages (what happened on startup)
journalctl -b | head -20  # First 20 lines of this boot's logs

# 5. CRITICAL: Understand the restart policy
sudo systemctl show docker -p Restart
sudo systemctl show docker -p RestartSec
# This explains: if Docker crashes, systemd will restart it automatically after N seconds
```

**Exercise**: Why would you set `Restart=always` on a production service? What could go wrong if you set `RestartSec=1s` (1 second)?

---

## 💾 PART 4: Storage, Disks & Backups

### Understanding Disk Storage

```bash
df -h                   # Disk space by filesystem (h = human readable)
du -sh /var/log/        # How much space this directory uses
lsblk                   # List all block devices (disks, partitions)
mount                   # What filesystems are mounted where
```

**HANDS-ON: DISK CRISIS DIAGNOSIS**

This ties to **Job Responsibility**: *"Design and implement scalable, reliable solutions to improve the efficiency and risk profile of technical platform."*

```bash
# 1. What's the actual disk usage RIGHT NOW?
df -h       # Human readable
df -h -i    # ALSO check inodes (can run out of inodes before disk space!)

# 2. Which directory is consuming the most space?
du -sh /* 2>/dev/null | sort -rh | head -10

# 3. Where are YOUR app's logs?
du -sh /var/log/ 2>/dev/null
ls -lhS /var/log/ | head -10  # Largest log files

# 4. Scenario: Your database backups are in /var/backups — how big?
du -sh /var/backups/ 2>/dev/null || echo "Not present yet"

# 5. CRITICAL: What happens when disk fills to 100%?
# Test by running:
df -h | tail -1          # Look at last line — this is where we're heading
# When any filesystem reaches 90%+ → databases START FAILING → pages go down
```

### The Critical Concept: Inodes

Every file uses 2 things: **disk space** (for the content) and an **inode** (for the metadata — name, permissions, timestamps). You can run OUT of inodes even if you have disk space left. This is a real production disaster.

```bash
df -i           # Check inode usage (not space, inodes)
# If you see "IUsed" > 80% of "Iavail", you have a problem
```

### Backups — The Pokevend Way

For our PostgreSQL database:
```bash
# The backup command — this is what saves the data when disaster strikes
pg_dump -h localhost -U pokevend_user pokevend_db > backup_$(date +%Y%m%d).sql

# To restore after a disaster:
psql -h localhost -U pokevend_user pokevend_db < backup_20260401.sql

# In production: compress it, encrypt it, ship it offsite
pg_dump -h localhost -U user dbname | gzip | openssl enc -aes-256-cbc -k "PASSWORD" > backup.sql.gz.enc
```

**HANDS-ON: UNDERSTAND BACKUPS (10 minutes)**

```bash
# 1. Where would Pokevend backups live?
ls -la /var/backups/ 2>/dev/null || echo "Directory doesn't exist yet"
mkdir -p /var/backups/pokevend
du -sh /var/backups/pokevend

# 2. How LARGE would a database dump be?
# (When we have actual data, you'll measure this)
echo "Database backup sizes matter because:"
echo "- Storage costs (GB × cost/month)"
echo "- Restore time (larger dump = longer to restore)"
echo "- Network cost (shipping backups offsite)"

# 3. Backup retention: How long to keep backups?
# This is a BUSINESS decision, not technical:
# Keep 7 daily backups (1 week of recovery)
# Keep 4 weekly backups (1 month of recovery)
# Keep 12 monthly backups (1 year of recovery)
```

---

## 🔐 PART 5: SSH — Secure Remote Access

**Job Qualification**: *"Comfort working in both Windows and Linux environments, including basic command-line usage."* + *"Understanding of basic cybersecurity principles, including access controls, segmentation, and secure configuration practices."*

### How SSH Works (Not Magic)

SSH uses **asymmetric cryptography** (public/private key pairs):
1. You generate a key pair: `ssh-keygen -t ed25519`
2. Your **private key** stays on YOUR machine (NEVER share this)
3. Your **public key** gets put on the server in `~/.ssh/authorized_keys`
4. When you connect, the server sends a random challenge
5. Only your private key can sign it correctly — no password needed

### SSH Hardening (What Real Engineers Do):

```bash
# /etc/ssh/sshd_config — The SSH server config
PermitRootLogin no              # NEVER allow root to SSH in directly
PasswordAuthentication no       # ONLY allow key-based auth (disable passwords)
PubkeyAuthentication yes        # Require keys
AllowUsers iscjmz               # Whitelist specific users
Port 2222                       # Change from default port 22 (minor security gain)
MaxAuthTries 3                  # Only 3 attempts before disconnect
```

```bash
# After editing, restart SSH (be careful — have a backup connection open!)
sudo systemctl restart sshd
```

**HANDS-ON: GENERATE YOUR SSH KEY (5 minutes)**

```bash
# 1. Check if you already have a key
ls -la ~/.ssh/
# If id_ed25519 exists, you already have a key. If not:

# 2. Generate a NEW Ed25519 key (faster and more secure than RSA)
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "iscjmz@workstation"
# -t ed25519 = use Ed25519 algorithm
# -f = filename
# -N "" = no password (OK for dev/test; production should have password)
# -C = comment to identify the key

# 3. See your public key (this is what you put on servers)
cat ~/.ssh/id_ed25519.pub

# 4. NEVER show your private key, but verify it exists
ls -l ~/.ssh/id_ed25519

# 5. Connect to a server (when we have Pokevend deployed):
# ssh -i ~/.ssh/id_ed25519 pokevend-svc@pokevend-server.internal
```

---

## 📋 PRE-REQUISITES BEFORE STARTING WEEK 1 SCRIPTS

**Goal**: Build a baseline understanding of YOUR system before you start modifying it. Ask: "If this breaks, can I diagnose it?"

```bash
# RUN ALL OF THESE RIGHT NOW and observe the output

# ──── System Identity ─────────────────────────
echo "=== YOUR SYSTEM ==="
uname -a                    # Kernel version and architecture
cat /etc/os-release         # What Linux distro
uptime                      # Uptime and load average
free -h                     # RAM usage
df -h                       # Disk usage

# ──── Users and Access Control ─────────────────
echo ""
echo "=== USERS & ACCESS ===
id                          # Who are you? What groups?
cat /etc/passwd | grep -v nologin | cut -d: -f1  # Real users
sudo cat /etc/sudoers       # Who has root access

# ──── Running Services ─────────────────────────
echo ""
echo "=== SERVICES RUNNING ==="
systemctl list-units --type=service --state=running --no-pager | head -10
ps aux --sort=-%mem | head -5   # Top processes by memory

# ──── Network & Listening Ports ───────────────
echo ""
echo "=== NETWORK STATE ===" 
ss -tlnp | head -15             # All listening ports
hostname                        # Your machine name
ip addr | grep "inet " | grep -v "127."   # Your IP addresses

# ──── Docker/Containers ───────────────────────
echo ""
echo "=== DOCKER STATE ===" 
docker ps 2>/dev/null || echo "Docker not running or not installed"
docker-compose ps 2>/dev/null || echo "No docker-compose running"
```

**After you run these commands, you should be able to answer:**
1. Is my machine under load? (Check load average vs CPU count)
2. How much disk space do I have? (Is anything > 80%?)
3. What users can access this machine? (id, sudoers)
4. What services are already running? (systemctl list-units)
5. If Pokevend crashes, how would I find the logs? (journalctl command)

**If you can explain what every line above outputs, you are ready for Week 1.**

---

## 🔗 External Resources

- **Linux man pages**: `man <command>` in your terminal for ANY command
- **The Linux Command Line (Book)**: https://linuxcommand.org/tlcl.php — Free, read chapters 1-10
- **Systemd in depth**: https://systemd.io/
- **chmod calculator**: https://chmod-calculator.com/ — Use this until octal clicks
- **explainshell.com**: Paste any bash command and it explains EVERY part
