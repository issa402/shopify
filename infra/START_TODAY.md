# 🚀 QUICK START: Today's Task
## What to do RIGHT NOW

Pick ONE of these based on where you are:

---

## 🟢 IF YOU HAVEN'T STARTED YET
### Start Here: Week 1, Day 1 (2-3 hours today)

```bash
# 1. Read the filesystem fundamentals
cat infra/lessons/01_linux_mastery.md | head -200

# 2. Run these commands and write down what they show:
whoami
id
pwd
ls -la /
df -h
du -sh ~/.

# 3. Run the first hands-on exercise
cd infra/lessons
grep -A 50 "HANDS-ON EXERCISE: Map Your System" 01_linux_mastery.md
# (Execute each command in that section)

# 4. Document your findings
cat > /tmp/day1_findings.txt << 'EOF'
My username: $(whoami)
My UID/GID: $(id)
Filesystems: $(df -h | head -10)
Home directory size: $(du -sh ~/)
EOF

# 5. Move to Day 2 tomorrow
```

---

## 🟡 IF YOU'RE PARTWAY THROUGH WEEK 1
### Week 1, Day 5: Build Real Scripts (3-4 hours)

```bash
# Read the script that needs TODOs filled in
cat infra/scripts/linux/01_os_audit.sh

# See what's marked TODO:
grep -n "TODO" infra/scripts/linux/01_os_audit.sh

# Test what's already there:
bash infra/scripts/linux/01_os_audit.sh

# Open in editor and start filling in TODOs
# You should implement:
# - audit_system_identity()
# - audit_users()
# - audit_processes()
# - audit_storage()
# - audit_docker()

# After each function, test:
bash infra/scripts/linux/01_os_audit.sh
```

---

## 🔵 IF YOU'VE FINISHED WEEK 1
### Start Week 2, Day 1: Bash Foundations (2-3 hours)

```bash
# 1. Read bash safety principles
cat infra/lessons/02_scripting_mastery.md | head -300

# 2. See the safety exercise
grep -A 30 "HANDS-ON: PROVE WHY THESE MATTER" infra/lessons/02_scripting_mastery.md

# 3. Create a test file
cat > /tmp/test_safety.sh << 'EOF'
#!/bin/bash
# Without set -e, this succeeds even though it fails:
cd /nonexistent
echo "If you see this, set -e wasn't working!"
EOF

bash /tmp/test_safety.sh  # It still succeeds — BAD

# 4. Now with set -euo pipefail:
cat > /tmp/test_safety_good.sh << 'EOF'
#!/bin/bash
set -euo pipefail
cd /nonexistent
echo "If you see this, set -euo pipefail wasn't working!"
EOF

bash /tmp/test_safety_good.sh  # Now it fails immediately — GOOD

# 5. Understand the difference
echo "Exercise complete! The second one is safer."
```

---

## 🟣 IF YOU'RE IN WEEK 2
### Week 2, Day 2-3: Build bash_fundamentals.sh Functions (2-3 hours)

```bash
# 1. See what needs to be implemented
cat infra/scripts/bash/01_bash_fundamentals.sh | head -100

# 2. Check the TODOs:
grep -n "TODO" infra/scripts/bash/01_bash_fundamentals.sh

# 3. Start editing. Here's an example logging function:
cat > infra/scripts/bash/01_bash_fundamentals.sh << 'EOF'
#!/bin/bash
set -euo pipefail

# Logging Functions
log::info() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ℹ️  $msg" >&2
}

log::warn() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $msg" >&2
}

log::error() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $msg" >&2
    return 1
}

log::success() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $msg" >&2
}

# TODO: Implement log::step() with ━ dividers
# TODO: Implement require::command()
# TODO: Implement require::root()
# TODO: Implement require::env()
# TODO: Implement require::file()

# Test the logging functions
log::info "This is an info message"
log::warn "This is a warning"
log::success "This is a success message"
EOF

# 4. Test it works
bash infra/scripts/bash/01_bash_fundamentals.sh

# 5. Fill in the remaining TODOs and test again
```

---

## 🐍 IF YOU'RE IN WEEK 3
### Week 3, Day 1: Start Python Practice (2-3 hours)

```bash
# 1. See the exercises
cat infra/practice/python_practice.py | head -150

# 2. Run Exercise 1
python3 infra/practice/python_practice.py 1

# 3. Check what needs to be fixed (TODOs):
grep -n "TODO" infra/practice/python_practice.py | head -20

# 4. Open the file and complete Exercise 1:
# - Count occurrences of "DB connection failed"
# - Find the maximum duration_ms
# - Create a dict of message → count

# 5. Test your fix:
python3 infra/practice/python_practice.py 1

# 6. Move to Exercise 2 tomorrow
```

---

## 🎯 FOR WEEK 2-3: Weekly Bash Practice
### Daily: Run bash_practice.sh exercises (1-2 hours daily)

```bash
# Day 1: Exercise 1 - Variables
bash infra/practice/bash_practice.sh 1
# TODO: Extract the base name from a file path

# Day 2: Exercise 2 - Loops + Arrays
bash infra/practice/bash_practice.sh 2
# TODO: Count how many services are accessible
# (tests ports 8080, 5432, 6379)

# Day 3: Exercise 3 - Text Processing
bash infra/practice/bash_practice.sh 3
# TODO: Find partitions > 50% full

# Day 4: Exercise 4 - Functions
bash infra/practice/bash_practice.sh 4
# TODO: Implement check_disk_space() function

# Day 5: Exercise 5 - Deployment
bash infra/practice/bash_practice.sh 5
# TODO: Complete the build and deployment logic

# All together:
bash infra/practice/bash_practice.sh all
```

---

## HOW TO KNOW YOU'RE DONE FOR THE DAY

- ✅ You ran all the commands in the lesson
- ✅ You tried to understand what each line does
- ✅ You asked "why?" at least 3 times
- ✅ You completed one TODO or exercise
- ✅ You tested it works
- ✅ You wrote 2-3 sentences about what you learned

---

## IF YOU GET STUCK

1. **Read the lesson again** — Slowly. Line by line.
2. **Try the command manually** — Don't just copy-paste
3. **Check the error** — What does it say? Google it.
4. **Look at bash_fundamentals.sh** — Patterns are there to reuse
5. **Ask GPT/Claude** — "I got this error: [ERROR], what does it mean?"

---

## THE SCHEDULE

- **Days 1-4**: Read + Run exercises (4-8 hours)
- **Day 5**: Write (implement TODOs from scripts) (3-4 hours)
- **Days 6-7**: Review + Plan next week

If you get stuck on a TODO, **don't skip it**. That TODO is teaching you something you'll need later.

---

## RIGHT NOW, PICK ONE:

```
Week 1? → bash infra/scripts/linux/01_os_audit.sh
Week 2? → bash infra/practice/bash_practice.sh all
Week 3? → python3 infra/practice/python_practice.py 1
Week 4? → cat infra/lessons/03_networking_mastery.md | head -100
Week 5? → cat infra/lessons/04_cybersecurity_mastery.md | head -100
Week 6? → cat infra/lessons/05_cloud_mastery.md | head -100
```

Pick your week → Run your command → START.
