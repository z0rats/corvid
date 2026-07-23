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

log "Starting Corvid"
docker compose up -d

log "Waiting for backend to become healthy"
for _ in $(seq 1 30); do
  status="$(docker inspect --format '{{.State.Health.Status}}' backend 2>/dev/null || echo starting)"
  [ "$status" = "healthy" ] && break
  sleep 2
done

echo
log "Corvid is starting up in $INSTALL_DIR"
log "Open http://localhost:4000 in your browser"
log "Access token (first run): docker compose -f $INSTALL_DIR/docker-compose.yaml logs backend | grep -i token"
log "To update later: cd $INSTALL_DIR && ./update.sh"
