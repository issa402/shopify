# PokeAi

Free Pokemon card market-data CLI.

This service lives in `services/pokeai` inside the Shopify/NexusOS repo. It can be used as a local CLI or as a small LAN JSON API for other services/scripts.

Sources:

- PokemonTCG API: free/no-key card data, TCGPlayer prices, Cardmarket prices
- TCGdex: free multilingual card/set metadata
- PokeTrace: optional free API key for raw/graded pricing

## Commands

```powershell
python -B pokeai.py search "Charizard" --limit 10
python -B pokeai.py card gym2-2
python -B pokeai.py compare "Charizard" --limit 10
python -B pokeai.py watch add gym2-2
python -B pokeai.py watch list
python -B pokeai.py tcgdex "Charizard" --limit 5
```

## LAN API

Run a small JSON API for another computer on your network:

```powershell
python -B api_server.py --host 0.0.0.0 --port 8765 --allow-ip YOUR_LINUX_IP
```

Endpoints:

```text
GET /health
GET /search?q=Radiant%20Charizard&limit=10
GET /card/pgo-11
GET /watchlist
```

From the Linux computer:

```bash
curl http://WINDOWS_IP:8765/health
curl "http://WINDOWS_IP:8765/search?q=Radiant%20Blastoise&limit=5"
curl http://WINDOWS_IP:8765/card/pgo-18
```

To restrict the port at Windows Firewall too, run PowerShell as Administrator on Windows:

```powershell
New-NetFirewallRule -DisplayName "PokeAi API from Linux" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765 -RemoteAddress YOUR_LINUX_IP
```

Optional PokeTrace:

```powershell
copy .env.example .env
# add your free PokeTrace key
python -B pokeai.py poketrace cz_9921
```

The CLI writes cache files under `.cache/` to avoid hammering free APIs.

See [explanations.md](./explanations.md) for the short handoff notes, LAN commands, and networking terms used during setup.
