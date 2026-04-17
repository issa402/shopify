# PostgreSQL Mastery For Infrastructure And Database Administration

This file is for learning PostgreSQL like someone who has to run it, protect it, tune it, inspect it, and recover it.

Not just "write a `SELECT` statement."
Not just "know what a table is."
The goal here is to help you become the kind of engineer who can look at a Postgres system and understand:

- what it is doing
- how it stores data
- how clients connect to it
- how schema changes work
- how roles and permissions work
- how indexes affect performance
- how transactions and MVCC affect behavior
- how to back it up
- how to restore it
- how to inspect it when something goes wrong

And because you already have a real Postgres database in your Pokemon project, this guide is built around that system instead of some fake demo app.

## What A PostgreSQL Administrator Or Database-Focused Infrastructure Engineer Actually Does

A lot of people think "database work" means writing SQL queries.
That is part of it, but a database admin or infrastructure engineer cares about the entire system around the database.

That means things like:

- creating and managing databases
- creating and managing users and roles
- granting the right permissions and not too many
- understanding how applications connect
- understanding which tables are critical
- understanding indexes and why queries are slow
- understanding what happens during writes, updates, and deletes
- understanding vacuum, dead tuples, and MVCC
- understanding backup and restore
- understanding what would happen if the machine or container died
- understanding how to inspect table size, row count, and index usage
- understanding replication and point-in-time recovery at a high level

That is why Postgres is not just "SQL syntax."
It is a full operational system.

## Why This Matters For A Role Like Future Standard

The role talks about infrastructure, storage, compute, support, security, automation, troubleshooting, and data-driven thinking.

A production database sits right in the middle of those concerns.

If a database is unhealthy:
- apps fail
- background workers fail
- APIs slow down
- alerts stop firing
- writes time out
- the platform becomes unreliable

If a database is misconfigured:
- security risk goes up
- permissions break
- apps cannot connect
- migrations fail

If a database is not understood:
- schema changes become dangerous
- performance problems look mysterious
- recovery becomes terrifying

So yes, being genuinely strong with Postgres is very valuable for this kind of job.

## The First Mental Model: PostgreSQL Is A Running Service, Not Just A File

Treat PostgreSQL as a real service with all the normal infrastructure questions:

- where is it running
- what process is it
- what port is it listening on
- who can connect
- where is the data stored
- how do clients authenticate
- what is the schema
- what is the workload pattern
- what would happen if it dies

In your Pokemon project, Postgres is currently running inside Docker.
That means you should think about it in two layers:

### Layer 1: PostgreSQL as a database engine

This is the internal logic:
- tables
- rows
- indexes
- transactions
- MVCC
- vacuum
- WAL
- roles

### Layer 2: PostgreSQL as infrastructure

This is the operational side:
- container
- port mapping
- volume persistence
- credentials
- startup health
- backup and restore
- monitoring

You need both layers to become really good.

## What Your Actual Pokemon Postgres Setup Looks Like

You already have a real setup.
That is good news.

The database service is defined in [Pokemon/docker-compose.yml](/home/iscjmz/shopify/shopify/Pokemon/docker-compose.yml).
It uses a Postgres container, a persistent volume, environment variables for DB/user/password, and startup migrations.

Your schema starts in:
- [database/migrations/001_init.sql](/home/iscjmz/shopify/shopify/Pokemon/database/migrations/001_init.sql)
- [database/migrations/002_price_alerts.sql](/home/iscjmz/shopify/shopify/Pokemon/database/migrations/002_price_alerts.sql)

Your Go app connects through:
- [server/config/db.go](/home/iscjmz/shopify/shopify/Pokemon/server/config/db.go)

You already have a useful DB inspection script in:
- [scripts/db_report.py](/home/iscjmz/shopify/shopify/Pokemon/scripts/db_report.py)

This means you are not starting from zero.
You already have a real DB-backed service to learn from.

## What You Need To Know In Order

Do not try to learn all of Postgres in one giant mess.
Learn it in layers.

### Layer 1: SQL and schema fundamentals

You need to be strong with:

- `SELECT`
- `INSERT`
- `UPDATE`
- `DELETE`
- `WHERE`
- `JOIN`
- `GROUP BY`
- `ORDER BY`
- `LIMIT`
- `COUNT`
- `DISTINCT`
- constraints
- indexes

This is the basic language of the database.

### Layer 2: Database objects and structure

You need to understand:

- database
- schema
- table
- row
- column
- primary key
- foreign key
- unique constraint
- check constraint
- index
- trigger
- extension

Your migration files already show all of these.

### Layer 3: Operations and administration

You need to understand:

- roles and users
- connection strings
- auth basics
- startup and health
- backup
- restore
- permissions
- table inspection
- index inspection
- DB size

### Layer 4: Internal mechanics

You need to understand:

- transactions
- ACID at a practical level
- MVCC
- dead tuples
- vacuum
- WAL
- query planning
- locks

This is the part that separates "I know SQL" from "I understand Postgres deeply."

## The Most Important Practical Concepts

### 1. SQL is not the database

SQL is the language you use to ask the database to do work.
Postgres is the actual system that stores data, enforces constraints, plans queries, and manages transactions.

If someone says "be good at Postgres," they usually mean more than "can write a basic query."

### 2. Schema is part of system design

A database schema is not just a storage bucket.
It expresses system rules.

In your schema:
- `users.email` is unique
- `api_keys.user_id` references `users.id`
- `watchlists.user_id` references `users.id`
- `ON DELETE CASCADE` defines cleanup behavior
- indexes define likely query paths

That means the schema is part of the application’s correctness.

### 3. Indexes are about access paths

An index is not "free speed."
It is a tradeoff.

Indexes make reads for certain query patterns faster.
But they cost:
- disk space
- maintenance work on insert/update/delete

So good database people learn to ask:

- what queries are common
- what filters and joins do they use
- what indexes help those patterns
- which indexes exist but are never used

Your `db_report.py` already starts to teach this by reading `pg_stat_user_indexes`.

### 4. PostgreSQL uses MVCC

MVCC means Multi-Version Concurrency Control.

This is one of the most important Postgres concepts.
It is how Postgres lets readers and writers work at the same time without blocking each other all the time.

The short version is:

When a row is updated, Postgres often creates a new row version instead of overwriting the old one in place.

That means:
- readers can still see the old version depending on transaction visibility
- writers can create new versions
- dead row versions accumulate
- vacuum eventually cleans them up

This is why vacuum matters.
This is why dead tuples matter.
This is why understanding updates and long-running transactions matters.

You do not need to be scared of MVCC.
You just need to know that Postgres is not rewriting data the way beginners imagine.

## The Core CLI Tools You Need To Know

### `psql`

This is the Postgres command-line client.
If you want to get genuinely good, you need to be comfortable in `psql`.

You can connect to your containerized DB with:

```bash
docker exec -it pokemontool_postgres psql -U pokemontool_user -d pokemontool
```

Inside `psql`, the most useful meta-commands are:

```sql
\l
\c pokemontool
\dt
\d users
\d+ alerts
\du
\dn
\x
\q
```

Now the meaning:

`\l` lists databases.

`\c pokemontool` connects to the `pokemontool` database.

`\dt` lists tables.

`\d users` describes the `users` table.

`\d+ alerts` shows more detail, including storage-related info.

`\du` lists roles.

`\dn` lists schemas.

`\x` toggles expanded display, which is useful when rows are wide.

If you get comfortable with `psql`, you stop treating the database like a black box.

## Lab 1: Learn Your Actual Schema Like A Database Admin

### Goal

Stop thinking of your database as "whatever the app uses."
Start thinking of it as a system with explicit structure and rules.

### What to do

Connect with `psql`:

```bash
docker exec -it pokemontool_postgres psql -U pokemontool_user -d pokemontool
```

Then run:

```sql
\dt
\d users
\d api_keys
\d watchlists
\d alerts
\d inventory
\d shows
\d price_alerts_settings
```

### What to look for

Do not just skim the names.
Actually inspect:

- column names
- data types
- defaults
- primary keys
- foreign keys
- unique constraints
- indexes

### What you should understand after this

You should be able to answer:

- what the main business tables are
- which tables depend on `users`
- which columns are nullable
- which uniqueness rules are enforced in the DB
- what relationships the app depends on

### What to expect

You will see UUID keys, timestamps, foreign keys, and indexes.
That is good.
That means the schema is already teaching you real production patterns.

## Lab 2: Learn SQL The Right Way On Your Real Data

### Goal

Move from "I kind of know SQL" to "I can inspect and answer real questions from this system."

### Step 1: Simple reads

Run queries like:

```sql
SELECT * FROM users LIMIT 5;
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;
SELECT * FROM watchlists LIMIT 10;
```

### Step 2: Filtering and ordering

```sql
SELECT card_name, marketplace, price, created_at
FROM alerts
WHERE is_read = false
ORDER BY created_at DESC
LIMIT 20;
```

### Step 3: Aggregation

```sql
SELECT marketplace, COUNT(*) AS total_alerts
FROM alerts
GROUP BY marketplace
ORDER BY total_alerts DESC;
```

### Step 4: Joins

```sql
SELECT u.email, a.card_name, a.alert_type, a.created_at
FROM alerts a
JOIN users u ON a.user_id = u.id
ORDER BY a.created_at DESC
LIMIT 20;
```

### What this teaches

This teaches you that SQL is how you ask operational and business questions from a real system.

You are not just learning syntax.
You are learning how to inspect production-shaped data.

## Lab 3: Learn Constraints And Why They Matter

### Goal

Understand that the database is not just storing data.
It is enforcing rules.

### What to do

Inspect these concepts in your migration files:

- unique email in `users`
- foreign keys from child tables to `users`
- check constraint in `price_alerts_settings.direction`
- `ON DELETE CASCADE`

Then test one in a safe way.

For example, try inserting bad data into a throwaway row and see what error you get.

Example:

```sql
INSERT INTO price_alerts_settings (user_id, card_name, threshold, direction)
VALUES ('00000000-0000-0000-0000-000000000000', 'Charizard', 100.00, 'SIDEWAYS');
```

### What to expect

You should get an error because:
- the direction fails the check constraint
- and possibly the user_id fails the foreign key if no such user exists

### Why this matters

This is how strong systems defend themselves even if app logic messes up.

## Lab 4: Learn Indexing Through Your Real Tables

### Goal

Understand what indexes exist and why.

### What to do

Use `psql`:

```sql
\d alerts
\d watchlists
\d inventory
\d shows
```

Then inspect index usage with your script:

```bash
cd ~/shopify/shopify/Pokemon
python3 scripts/db_report.py
```

### What to look for

Look for:

- indexes on foreign keys
- partial indexes
- unused indexes

### Why this matters

An infrastructure or database-minded engineer should be able to say:

"This index exists because we often query unread alerts."

not just:

"There is an index there."

### Extra practice

Run:

```sql
EXPLAIN SELECT * FROM alerts WHERE user_id = 'some-user-id';
EXPLAIN ANALYZE SELECT * FROM alerts WHERE is_read = false;
```

This starts teaching you query planning.

`EXPLAIN` shows the plan Postgres thinks it will use.
`EXPLAIN ANALYZE` actually runs the query and shows what happened.

That is one of the most powerful performance learning tools in Postgres.

## Lab 5: Learn Roles, Permissions, And Access Control

### Goal

Understand that database security starts with roles and permissions.

### What a DBA cares about

Not every app or person should be a superuser.
Not every connection should be allowed to do schema changes.
Not every service should read every table.

### What to inspect

In `psql`:

```sql
\du
```

### What to learn conceptually

Postgres has:

- roles
- login roles
- privileges
- grants

Example commands to know:

```sql
CREATE ROLE report_reader LOGIN PASSWORD 'strong-password';
GRANT CONNECT ON DATABASE pokemontool TO report_reader;
GRANT USAGE ON SCHEMA public TO report_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO report_reader;
```

### Why this matters

This is what database least privilege looks like.

Even if you do not change your project roles right away, you should understand how you would create:

- an app role
- a read-only reporting role
- an admin role

That is real infrastructure skill.

## Lab 6: Learn Backup And Restore

### Goal

Understand that data is not real infrastructure unless you know how to recover it.

### The simplest backup tool

`pg_dump`

For your running container:

```bash
docker exec pokemontool_postgres pg_dump -U pokemontool_user -d pokemontool > pokemontool_backup.sql
```

This creates a logical SQL backup.

### Restore that backup

You can restore into a fresh DB with `psql`:

```bash
cat pokemontool_backup.sql | docker exec -i pokemontool_postgres psql -U pokemontool_user -d pokemontool
```

### What to understand

This is not point-in-time recovery.
This is a logical dump and restore.
It is still a critical skill.

### Why this matters

If someone says:

"Can you prove we can recover this database?"

you should not answer with vibes.

You should be able to say:

"Here is the backup procedure, here is the restore path, here is what we verified."

## High-Level Recovery Concepts You Need To Know

### WAL

WAL means Write-Ahead Log.
Postgres writes change records to WAL before the data changes are considered durable.

This supports:

- crash recovery
- replication
- point-in-time recovery

### Point-in-Time Recovery (PITR)

PITR means restoring the database to a specific time by combining:

- a base backup
- WAL files generated after that backup

This is deeper than `pg_dump`.
You may not need to fully implement it today, but you should absolutely understand what it is and why it matters.

Why:

If someone says:

"We accidentally deleted rows at 2:14 PM. Can we restore to 2:13 PM?"

that is a PITR-style question.

That is serious DBA thinking.

## Lab 7: Learn MVCC In A Way That Makes Sense

### Goal

Understand why updates and deletes are not as simple as they look.

### The practical explanation

Postgres keeps multiple row versions so readers and writers can coexist safely.
That is MVCC.

When rows are updated or deleted:
- old versions may still exist for transaction visibility
- dead tuples accumulate
- vacuum eventually cleans them

### What this means operationally

If you have lots of updates and deletes:
- table bloat can grow
- vacuum becomes important
- long transactions can delay cleanup

### What to inspect

Run:

```sql
SELECT relname, n_live_tup, n_dead_tup
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

### Why this matters

This starts teaching you to think like someone maintaining a live DB, not just querying it.

## Lab 8: Learn Query Planning And Performance

### Goal

Start understanding why some queries are fast and others are bad.

### What to do

Pick a few real queries from your app patterns and run:

```sql
EXPLAIN SELECT * FROM watchlists WHERE user_id = 'some-id';
EXPLAIN SELECT * FROM alerts WHERE is_read = false;
EXPLAIN ANALYZE SELECT * FROM shows WHERE start_date >= NOW();
```

### What to look for

Look for phrases like:

- Seq Scan
- Index Scan
- Bitmap Heap Scan
- cost
- actual time
- rows

### What this means

If a table gets large and Postgres uses a sequential scan, maybe that is fine.
Maybe it is terrible.
You need to learn to ask whether the access path matches the workload.

That is how database performance work begins.

## Lab 9: Learn Connection Paths And Infrastructure Side

### Goal

Understand how your apps actually reach Postgres.

### What to inspect

Read:
- [server/config/db.go](/home/iscjmz/shopify/shopify/Pokemon/server/config/db.go)
- [Pokemon/.env](/home/iscjmz/shopify/shopify/Pokemon/.env)
- [Pokemon/docker-compose.yml](/home/iscjmz/shopify/shopify/Pokemon/docker-compose.yml)

### What to understand

Your Go app builds a DSN and connects through a connection pool.
That means you should know:

- host
- port
- database name
- user
- password
- why pooling matters

### Why pooling matters

Opening a DB connection for every request is expensive.
A pool keeps reusable connections warm.

That is why `pgxpool` in [db.go](/home/iscjmz/shopify/shopify/Pokemon/server/config/db.go) matters.

This is very real infra/application overlap.

## Lab 10: Use Your Existing Database Report Script Like An Operator

### Goal

Learn to inspect a live database the way a support-minded engineer would.

### Run

```bash
cd ~/shopify/shopify/Pokemon
python3 scripts/db_report.py
```

### What it teaches

It teaches:

- table counts
- index usage
- recent activity
- whether the DB is even reachable

That is exactly the kind of operational tooling that makes infra teams faster.

## What You Should Practice Until It Feels Natural

You should keep working until these things feel normal:

- opening `psql`
- listing tables
- describing tables
- writing real `SELECT` queries
- joining tables
- reasoning about constraints
- understanding why indexes exist
- running `EXPLAIN`
- understanding connection strings
- understanding the difference between backup and PITR
- understanding how roles and privileges work
- understanding why MVCC and vacuum exist

That is how you get good.

## The Best Way To Use This With Your Project

Your best learning loop is:

1. Read one section of this guide.
2. Do the lab on your real Pokemon DB.
3. Write down what you observed.
4. Explain what would happen in production if that part broke.
5. Tie it back to app behavior.

That last step matters.

For example:

"If Postgres is unreachable, the Go API fails startup."

"If indexes are wrong, alerts queries slow down."

"If schema constraints are weak, bad app data gets stored."

"If backups are fake, the platform is one mistake away from real data loss."

That is how database mastery becomes infrastructure mastery.

## The Next Best Upgrade After This

Once you work through this file, the strongest next move is to make a second Postgres practice workbook with:

- explicit query drills
- explicit `psql` drills
- explicit backup/restore drills
- explicit indexing drills
- explicit MVCC and vacuum drills
- explicit role/permission drills
- explicit Pokemon-specific admin scenarios

That would turn this guide into a full DBA lab manual.
