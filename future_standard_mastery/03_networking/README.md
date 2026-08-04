# 03 Networking

This section teaches you how to think about communication paths between systems.

Most people think they understand networking until something times out.
Then they realize they only knew vocabulary, not flow.

## What Networking Means In Infrastructure Work

Networking is the answer to questions like:

- how does traffic reach the service
- what name resolves to what IP
- which process is listening on which port
- what systems can talk to each other
- what should be public and what should stay internal
- where can requests fail on the path

## What This Would Look Like At Future Standard

Examples:

- diagnosing why an internal app is unreachable
- checking whether DNS, routing, firewalling, or the app itself is the problem
- reviewing whether a service is exposing an internal port publicly
- mapping which services should be segmented from each other
- validating trust boundaries between users, apps, and internal infrastructure

## Learn This First

### Port vs route

A port is where a process listens.
A route is the application path like `/health` or `/api/login`.

If port `8080` is closed, the route does not matter because you never reached the app.

### DNS vs connectivity

If DNS fails, you may never reach the right IP.
If DNS works but the port is closed, name resolution is fine but the service path still fails.

### Connection refused vs timeout

Connection refused usually means:
- nothing is listening there
- or the listener is rejecting

Timeout often suggests:
- firewall issue
- dependency hang
- routing issue
- service too slow to respond

That distinction matters a lot.

## Pokemon Lab 1: Build The Port And Protocol Map

### Goal

Turn Pokemon into a real network diagram in your head.

### Files to inspect

- [Pokemon/docker-compose.yml](/home/iscjmz/shopify/shopify/Pokemon/docker-compose.yml)
- [Pokemon/server/routes/routes.go](/home/iscjmz/shopify/shopify/Pokemon/server/routes/routes.go)
- [Pokemon/client/src/services/api.js](/home/iscjmz/shopify/shopify/Pokemon/client/src/services/api.js)

### Exact task

For each major service, record:
- port
- protocol
- public or internal
- who calls it
- what breaks if it is unreachable

### Why this matters

Because a good infrastructure engineer can answer:
"What is supposed to talk to what, and over which path?"

## Pokemon Lab 2: Trace One Browser Request

### Goal

Practice following a full request from user to dependency.

### Exact task

Pick one user flow:
- login
- watchlist load
- alerts view

Then trace:

1. browser request
2. frontend API call
3. server route
4. downstream dependency calls
5. database or cache path
6. async side effects if any

### Why this matters

Because once you can trace one request end-to-end, production debugging becomes much more grounded.

## Pokemon Lab 3: Trace One Queue Event

### Goal

Understand that networking is not only HTTP.

### Exact task

Pick one RabbitMQ-related flow and answer:

- who publishes the message
- what queue/exchange path it uses
- who consumes it
- what happens if delivery pauses
- what happens if consumers fail

### Why this matters

Because infrastructure roles care about event flow just as much as request flow.
