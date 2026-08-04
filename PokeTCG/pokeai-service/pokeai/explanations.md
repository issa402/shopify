# PokeAi Notes

## What We Built

PokeAi started as a local Pokemon card price CLI. We added `api_server.py`, a small JSON backend using Python's built-in HTTP server, so another computer on the same network can call it over HTTP.

The backend wraps the existing `pokeai.py` functions. It does not need Flask, FastAPI, or any extra Python package.

## Main Commands

Run CLI searches:

```bash
python -B pokeai.py search "Radiant Charizard" --limit 10
python -B pokeai.py card pgo-11
python -B pokeai.py watch list
```

Start the LAN API:

```bash
python -B api_server.py --host 0.0.0.0 --port 8765 --allow-ip 192.168.1.12
```

Test from another computer:

```bash
curl http://WINDOWS_OR_SERVER_IP:8765/health
curl "http://WINDOWS_OR_SERVER_IP:8765/search?q=Radiant%20Charizard&limit=5"
curl http://WINDOWS_OR_SERVER_IP:8765/card/pgo-11
```

Stop the API by process id on Windows:

```powershell
Stop-Process -Id PROCESS_ID
```

## Networking Terms

`0.0.0.0` means "listen on all network interfaces", not just localhost.

`127.0.0.1` means only the same machine can call it.

`--port 8765` means the service listens on TCP port `8765`.

`--allow-ip` is an app-level allowlist. If the caller IP is not listed, the API returns `403 forbidden`.

`192.168.101.66/24` means the IP is `192.168.101.66`; `/24` is the subnet mask, not part of the single host address.

Windows Firewall should also allow the port if this runs on Windows:

```powershell
New-NetFirewallRule -DisplayName "PokeAi API from Linux" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765 -RemoteAddress LINUX_IP
```

## Endpoints

```text
GET /health
GET /search?q=NAME&limit=10
GET /card/CARD_ID
GET /watchlist
```

## What Happened During Testing

The Linux machine reached the Windows API successfully, so the LAN path worked. One failure returned `502 Bad Gateway`; that meant the API was reachable, but the Windows process could not reach the upstream PokemonTCG pricing API at that moment.

For moving this to Linux, run the same Python commands there and call `localhost` or the Linux server IP instead of the Windows IP.
