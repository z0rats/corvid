---
title: Access from Another Device
description: Reaching Corvid from your LAN or a server, and putting HTTPS in front of it.
sidebar:
  order: 35
---

Out of the box Corvid listens on port `4000` on every network interface, and the backend accepts
any `Host` header (`API_TRUSTED_HOSTS=["*"]`), so `http://<server-ip>:4000` or
`http://<hostname>:4000` works from other devices without extra configuration. The access token
is what protects the API.

That connection is plain HTTP, though: the access token and everything you look up travel
unencrypted across the network. On anything other than `localhost`, put an HTTPS reverse proxy
in front of Corvid.

## HTTPS with Caddy

[Caddy](https://caddyserver.com/) obtains and renews certificates automatically. Install it on
the same host as Corvid, then use a `Caddyfile` like this:

```
corvid.example.com {
    reverse_proxy localhost:4000
}
```

For a name that only exists on your LAN (no public DNS, so no Let's Encrypt certificate), use
Caddy's own local certificate authority instead:

```
corvid.lan {
    tls internal
    reverse_proxy localhost:4000
}
```

Browsers warn about `tls internal` certificates until Caddy's root CA is trusted on each client
device (`caddy trust` does this on the Caddy host itself).

No extra proxy settings are needed for Corvid's long-running scans or file uploads: Caddy streams
responses and imposes no read timeout or body-size limit by default.

## Close the plain-HTTP port

Once the proxy works, stop exposing port `4000` to the network so the unencrypted path can't be
used by mistake. In `.env`:

```
FRONTEND_PORT=127.0.0.1:4000
```

Then `docker compose up -d` to apply it. Corvid is now reachable only through the proxy.

## Optional: restrict accepted hostnames

To reject requests that arrive under any name other than your own, narrow
`API_TRUSTED_HOSTS` in `.env`, e.g. `API_TRUSTED_HOSTS=["corvid.example.com","localhost"]`
(keep `localhost` so the container health check still passes).
