# Self-Hosting Friend Access Guide

This guide explains how to run the Pokemon app on this Linux machine and let a friend access it without paying for cloud hosting.

The safest free setup is:

```text
Friend browser
  -> VPN/Tailscale private IP
  -> this Linux machine
  -> Pokemon client container
  -> internal Docker network
  -> Go API, PokeTCG, eBay scanner, Postgres, Redis, RabbitMQ
```

Only the web client should be reachable by your friend. Databases, Redis, RabbitMQ, and internal service ports should stay private.

## Current Local Apps

There are two separate app stacks in this repo:

- `Pokemon/`: the card watchlist, alerts, PokeTCG, eBay scanner, inventory, slabs, and pricing app.
- repo root Shopify/NexusOS stack: the future commerce/storefront/operator layer.

For friend testing, start with the Pokemon app.

## Start Pokemon Locally

From the repo root:

```bash
cd /home/iscjmz/shopify/shopify/Pokemon
docker compose up -d
```

Check status:

```bash
docker compose ps
```

Expected important services:

- `client`: frontend, usually exposed on `localhost:5173`
- `server`: Go API, usually exposed on `localhost:3001`
- `api-consumer`: Python eBay scanner
- `poketcg`: PokeTCG market data API
- `postgres`
- `redis`
- `rabbitmq`

Open locally:

```text
http://localhost:5173
```

## Start Pokemon For LAN Or VPN Testing

Use the self-host override when another device needs to open the app.

```bash
cd /home/iscjmz/shopify/shopify/Pokemon
docker compose -f docker-compose.yml -f docker-compose.selfhost.yml up -d postgres redis rabbitmq poketcg server api-consumer client
```

This uses:

- `Pokemon/docker-compose.yml`: normal app services.
- `Pokemon/docker-compose.selfhost.yml`: exposes only the client to LAN/VPN and keeps the Go API bound to localhost.

The command intentionally starts the core services only. Some optional services, such as the older scraping service or analytics engine, may need separate dependency fixes and are not required for the first friend-access test.

Current tested shape:

```text
outside browser -> this machine:5173 -> client nginx -> internal Docker server:3001
```

That means your friend opens the client, and the client container talks to the backend privately over Docker.

## Test From Your Other Wi-Fi

This machine's current LAN IP is:

```text
192.168.1.12
```

From another device, try:

```text
http://192.168.1.12:5173
```

If it loads, your other Wi-Fi can reach this machine.

If it does not load, likely causes are:

- the second Wi-Fi is a guest network and blocks device-to-device traffic
- the two Wi-Fi networks are on different subnets/VLANs
- the Linux firewall blocks port `5173`
- Docker client container is not running

Check the server machine:

```bash
cd /home/iscjmz/shopify/shopify/Pokemon
docker compose -f docker-compose.yml -f docker-compose.selfhost.yml ps
```

Check the listening port:

```bash
ss -ltnp | grep ':5173'
```

Expected:

```text
0.0.0.0:5173
```

If you see only `127.0.0.1:5173`, other devices cannot connect.

## Test From Phone Hotspot Or Cellular

If your phone is on cellular, `http://192.168.1.12:5173` will not work. That IP is private LAN-only.

For outside-your-house access without cloud hosting, use one of these:

- Tailscale or ZeroTier VPN: recommended for friends/testers.
- Router port forwarding plus HTTPS reverse proxy: only when you are ready to expose a public service.

Do not port-forward raw Docker service ports.

## Stop Pokemon

Stop everything but keep containers/volumes:

```bash
cd /home/iscjmz/shopify/shopify/Pokemon
docker compose stop
```

Stop and remove containers/networks while keeping database volumes:

```bash
cd /home/iscjmz/shopify/shopify/Pokemon
docker compose down
```

Do not use `docker compose down -v` unless you intentionally want to delete local database data.

## Stop Shopify Containers

The root Shopify dev containers are separate from Pokemon.

Stop only the three app containers by name:

```bash
docker stop shopify-web-1 shopify-gateway-1 shopify-ai-1
```

Or stop them through the correct compose file:

```bash
cd /home/iscjmz/shopify/shopify
docker compose -f docker-compose.dev.yml stop web gateway ai
```

If `docker compose stop` did not stop them before, it was probably run from the wrong directory or against the wrong compose project.

## Best Free Friend Access: Tailscale

Use this when only trusted friends need access.

Why this is best:

- no router port forwarding
- no public internet exposure
- encrypted private network
- easier firewall rules
- friend accesses your machine by private VPN IP

Basic flow:

1. Install Tailscale on this Linux machine.
2. Install Tailscale on your friend's machine.
3. Log both into the same Tailscale network.
4. Find this machine's Tailscale IP.
5. Friend opens:

```text
http://TAILSCALE_IP:5173
```

Example:

```text
http://100.x.y.z:5173
```

With this setup, your friend does not need to be on your Wi-Fi and does not need your home public IP.

As of May 2026, Tailscale Personal is free for this use case: up to 6 users and unlimited user devices. That is enough for you plus a few friends testing the app.

Install on this Linux machine:

```bash
curl -fsSL https://tailscale.com/install.sh -o /tmp/tailscale-install.sh
sudo sh /tmp/tailscale-install.sh
sudo tailscale up
tailscale ip -4
```

After `sudo tailscale up`, Tailscale prints a login URL. Open it, sign in, and approve this machine.

Then start the Pokemon app:

```bash
cd /home/iscjmz/shopify/shopify/Pokemon
docker compose -f docker-compose.yml -f docker-compose.selfhost.yml up -d postgres redis rabbitmq poketcg server api-consumer client
```

Your friend installs Tailscale, joins the same tailnet, then opens:

```text
http://YOUR_TAILSCALE_IP:5173
```

Do not give them `192.168.1.12` unless they are on your same LAN. For remote friends, use the Tailscale IP.

## Firewall Rule For VPN Access

Allow the frontend port only on the VPN interface.

If using UFW and Tailscale:

```bash
sudo ufw allow in on tailscale0 to any port 5173 proto tcp
sudo ufw deny 3001/tcp
sudo ufw deny 5432/tcp
sudo ufw deny 6379/tcp
sudo ufw deny 5672/tcp
sudo ufw deny 15672/tcp
```

Notes:

- `5173` is the client.
- `3001` is the Go API and should not be directly public if the client proxies API requests.
- `5432` Postgres must never be public.
- `6379` Redis must never be public.
- `5672` RabbitMQ must never be public.
- `15672` RabbitMQ management UI must never be public.

If the frontend cannot reach the API, check whether the client is built to proxy `/api` through its container. The preferred public shape is still one exposed web entrypoint, not many exposed service ports.

## Public Internet Option

Only do this when you understand the risk.

Public setup:

```text
Internet
  -> router port forward 443 only
  -> Linux firewall allows 443 only
  -> reverse proxy
  -> Pokemon client/API route
  -> private Docker services
```

Use a reverse proxy such as Caddy, Nginx, or Traefik. Do not port-forward Postgres, Redis, RabbitMQ, PokeTCG, or internal scanner services.

Recommended public ports:

- `443/tcp`: HTTPS
- `80/tcp`: optional, usually only for HTTP-to-HTTPS redirect or certificate setup

Avoid exposing:

- `3001`
- `5432`
- `6379`
- `5672`
- `15672`
- internal PokeTCG port
- internal scanner ports

## Public Hosting Checklist

Before letting random internet traffic hit the app:

- authentication must be enabled
- no dev bypass auth
- strong app secrets
- HTTPS only
- API rate limiting
- no database ports exposed
- no RabbitMQ management UI exposed
- no Redis exposed
- logs checked for secrets
- backups for Postgres
- clear eBay API quota limits

For early testing, use Tailscale instead of public hosting.

## How Containers Talk Safely

Docker services in the same compose project talk by service name:

```text
client -> server:3001
server -> postgres:5432
server -> redis:6379
server -> rabbitmq:5672
server -> poketcg:8765
api-consumer -> server:3001
```

Your friend does not need access to those internal names. Your friend only needs access to the web entrypoint.

## Billion-Dollar Direction

The Pokemon app is the product engine:

- exact card search
- raw market price
- slab-specific eBay observations
- below-market watchlist alerts
- inventory valuation
- potential repricing and deal-scoring

Shopify should be the commerce engine:

- storefront
- draft product creation
- checkout
- orders
- customer history
- seller subscriptions

The strongest business path is not a generic consumer price checker. The stronger path is a seller tool:

```text
Find undervalued cards
  -> alert fast
  -> track inventory and cost basis
  -> recommend listing price
  -> create Shopify draft listing
  -> seller reviews and publishes
  -> track sales and repricing
```

First sellable version:

- card shop or reseller logs in
- adds inventory
- sees current market value and margin
- watches for below-market buying opportunities
- pushes selected inventory to Shopify as draft products
- pays monthly for workflow speed and better decision-making

Do not force Shopify into the app until the workflow is clear. The first useful Shopify slice should be:

```text
Pokemon inventory item
  -> Prepare Listing
  -> suggested price and margin
  -> create Shopify draft product
  -> seller reviews in Shopify
```

That is how Shopify starts making sense: PokemonTool finds and values the opportunity, Shopify helps sell it.
