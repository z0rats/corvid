---
title: Route Outbound Traffic Through a VPN
description: Hiding the server's IP from the services and targets Corvid contacts.
sidebar:
  order: 37
---

Every lookup Corvid makes — IOC providers, username and email checks, scrapers, Amass, subfinder —
leaves from the backend container, so the services and sites it contacts see your server's public
IP. Only Email Search has its own proxy/Tor setting. To cover everything, including the external
binaries, route the whole backend container through a VPN client container at the network level.
This needs no change to Corvid itself.

The example uses [gluetun](https://github.com/passteque/gluetun) (image `qmcgaw/gluetun`), a VPN
client container supporting many providers; any VPN container that other containers can share a
network namespace with works the same way.

## Setup

Create `docker-compose.override.yaml` next to `docker-compose.yaml` (Compose loads it
automatically, for both the one-line-installer and the source-build setup):

```yaml
services:
  vpn:
    image: qmcgaw/gluetun
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun:/dev/net/tun
    environment:
      # Your VPN provider and credentials - see gluetun's documentation.
      - VPN_SERVICE_PROVIDER=...
    networks:
      corvid-network:
        # The frontend's nginx proxies to `backend:8000`; this alias makes that name resolve
        # to the VPN container, whose network the backend now shares.
        aliases:
          - backend
    # Source-build setup only: move the backend's host mapping here (used for a host-run Ollama).
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped

  backend:
    network_mode: "service:vpn"
    networks: !reset []
    extra_hosts: !reset []
    depends_on:
      - vpn
```

Then `docker compose up -d`.

The VPN container must accept inbound TCP connections on port `8000` from the Compose network
(that's how the frontend reaches the backend). If it runs its own firewall, as gluetun does, allow
that port per its documentation — otherwise the UI loads but every API call fails.

## Verify there's no leak

Check the IP the backend's traffic actually leaves from — it should be the VPN's, not your
server's:

```bash
docker compose exec backend python3 -c "import urllib.request; print(urllib.request.urlopen('https://api.ipify.org').read().decode())"
```

Re-check after VPN or Compose changes. A misconfigured override can silently fall back to the
server's own connection; a VPN container with a kill switch (gluetun has one) blocks traffic
instead when the tunnel is down, so Corvid's lookups fail rather than leak.
