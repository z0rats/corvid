#!/usr/bin/env bash
# Update (or roll back) a Corvid deployment installed via install.sh. Run from the
# install directory (where docker-compose.yaml lives), or as ./update.sh.
#
#   ./update.sh          # latest release
#   ./update.sh 2.3.0    # a specific release, e.g. to roll back
#
# The chosen version is recorded as CORVID_VERSION in .env, so later plain
# `docker compose` commands keep using it. Rolling back past a database migration
# also needs the pre-upgrade backup restored first - see the docs' "Rolling back".
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

version="${1:-latest}"
version="${version#v}"
if [ "$version" != "latest" ] && ! [[ "$version" =~ ^[0-9]+\.[0-9]+(\.[0-9]+)?$ ]]; then
  echo "error: version must be 'latest' or a release number like 2.4.0 (got '$1')" >&2
  exit 1
fi

# Rewrite in place (cat >, not mv) so .env keeps its own permissions.
touch .env
{ grep -v '^CORVID_VERSION=' .env || true; echo "CORVID_VERSION=$version"; } > .env.tmp
cat .env.tmp > .env
rm -f .env.tmp

echo "==> Pulling Corvid $version images"
docker compose pull

echo "==> Recreating containers"
docker compose up -d

echo "==> Removing superseded Corvid images"
docker image prune -f --filter "label=org.opencontainers.image.source=https://github.com/z0rats/corvid" >/dev/null

echo "==> Done"
