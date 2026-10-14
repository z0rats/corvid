#!/usr/bin/env bash
# One-line installer for Corvid: pulls pre-built images from GHCR and starts
# the app via Docker Compose. Usage:
#   curl -fsSL https://raw.githubusercontent.com/z0rats/corvid/main/install.sh | bash
# Override the install directory with CORVID_DIR=/path/to/dir before running.
set -euo pipefail

REPO="z0rats/corvid"
RAW_BASE="https://raw.githubusercontent.com/${REPO}/main"
INSTALL_DIR="${CORVID_DIR:-$HOME/corvid}"

log() { printf '==> %s\n' "$1"; }
die() { printf 'error: %s\n' "$1" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || die "Docker is required. Install it first: https://docs.docker.com/engine/install/"
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 plugin is required (the 'docker compose' command)."
# --wait (Compose 2.1.1+) blocks until every service reports healthy and fails if one doesn't.
docker compose up --help 2>/dev/null | grep -q -- '--wait' \
  || die "Docker Compose is too old (no 'up --wait'). Update the Compose plugin and re-run."

mkdir -p "$INSTALL_DIR/data"
cd "$INSTALL_DIR"

fetch() {
  local url="$1" dest="$2"
  curl -fsSL "$url" -o "$dest" || die "failed to download $url"
}

if [ -f docker-compose.yaml ]; then
  log "docker-compose.yaml already exists in $INSTALL_DIR, leaving it as-is"
else
  log "Downloading docker-compose.yaml"
  fetch "$RAW_BASE/docker-compose.prod.yaml" docker-compose.yaml
fi

if [ -f .env ]; then
  log ".env already exists in $INSTALL_DIR, leaving it as-is"
else
  log "Downloading .env.example as .env"
  fetch "$RAW_BASE/.env.example" .env
fi

log "Downloading update.sh"
fetch "$RAW_BASE/update.sh" update.sh
chmod +x update.sh

log "Pulling images"
docker compose pull

log "Starting Corvid (waiting for it to become healthy)"
docker compose up -d --wait \
  || die "Corvid failed to start. Check 'docker compose logs backend' in $INSTALL_DIR."

echo
log "Corvid is running in $INSTALL_DIR"
log "Open http://localhost:4000 in your browser"

# Read from inside the container: on the host, data/.access_token is owned by the container's
# UID 1000 with mode 0600, so a host user with a different UID can't read it.
if token="$(docker compose exec -T backend cat data/.access_token 2>/dev/null)" && [ -n "$token" ]; then
  log "Access token: $token"
else
  log "Access token: not generated (custom API_ACCESS_TOKEN in .env) - check 'docker compose logs backend' if unsure"
fi

log "Opening it from other devices? Put HTTPS in front first: https://z0rats.github.io/corvid/getting-started/remote-access/"
log "To update later: cd $INSTALL_DIR && ./update.sh"
