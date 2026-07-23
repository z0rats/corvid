#!/usr/bin/env bash
# Manually update a Corvid deployment installed via install.sh: pulls the
# latest images and recreates containers. Run from the install directory
# (where docker-compose.yaml lives), or as ./update.sh.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "==> Pulling latest images"
docker compose pull

echo "==> Recreating containers"
docker compose up -d

echo "==> Removing dangling images"
docker image prune -f >/dev/null

echo "==> Done"
