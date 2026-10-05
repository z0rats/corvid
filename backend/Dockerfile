FROM ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21 AS uv

# Compiles this repo's Go-based OSINT tools (subfinder, httpx, amass) from source
# rather than pulling prebuilt release binaries, since none of these projects
# publish per-arch checksums convenient to pin here and this repo's release images
# are multi-arch (amd64/arm64) - `go install` resolves the right arch for whichever
# platform buildx is building. Each pinned to an exact tag, like every other
# dependency in this repo (amass/httpx need a newer Go toolchain than subfinder's
# own go.mod requires, but a toolchain happily builds an older-declared module, so
# one stage/image covers all three). CGO_ENABLED=0 produces fully static binaries
# with no runtime dependency on this stage's (musl-based) libc, so they drop
# straight into the glibc-based runtime stage below.
FROM golang:1.26-alpine@sha256:ce864e7223ac17b1775e6fd0b4c0db580c2eb50e7953a427916379e4b92a1628 AS go-tools-builder
ENV CGO_ENABLED=0 GOBIN=/go/bin
RUN apk add --no-cache git ca-certificates
RUN --mount=type=cache,target=/root/.cache/go-build,id=go-build-cache \
    --mount=type=cache,target=/go/pkg/mod,id=go-mod-cache \
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@v2.16.0 && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@v1.12.0 && \
    go install -v github.com/owasp-amass/amass/v5/cmd/amass@v5.1.1 && \
    go install -v github.com/owasp-amass/amass/v5/cmd/ae_isready@v5.1.1

# GHunt in its own isolated venv, not the main one below: `ghunt>=2.3.2` requires `rich<14`,
# which conflicts with the main venv's pinned `mitreattack-python==6.2.0` (-> `rich==15.0.0`) -
# see docs/adr/0018-isolated-tool-cli-venvs.md for the general pattern this formalizes. Called at
# runtime via its absolute path (`ghunt_config.GHUNT_BIN`), never through `PATH`, same reasoning
# as the Go `httpx`/`httpx-probe` rename above. Needs the same build toolchain as the main
# `builder` stage below (not just a bare interpreter): GHunt depends on Pillow, which has no
# prebuilt wheel yet for this image's Python 3.14 and falls back to compiling from source.
FROM python:3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6 AS ghunt-builder
COPY --from=uv /uv /usr/local/bin/uv
RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache-ghunt-builder,sharing=locked \
    apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    zlib1g-dev \
    libjpeg-dev
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache-ghunt \
    uv venv /opt/tools/ghunt && \
    uv pip install --python /opt/tools/ghunt/bin/python ghunt==2.3.4

FROM python:3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6 AS builder
WORKDIR /backend

COPY --from=uv /uv /usr/local/bin/uv

RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache-builder,sharing=locked \
    apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libxml2-dev \
    libxslt-dev \
    liblzma-dev \
    zlib1g-dev

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Installed in its own layer, pinned to match requirements.txt, so unrelated
# requirements.txt changes don't invalidate this cache and force a rebuild.
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache \
    uv pip install "lxml[html-clean]==6.1.3"

COPY ./requirements.txt /backend/
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache \
    uv pip install --upgrade -r /backend/requirements.txt


FROM python:3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6
WORKDIR /backend

# Stamped from the release tag by CI (see .github/workflows/release.yml); falls
# back to this default for local builds and non-tagged CI images.
ARG VERSION=0.0.0-dev
ENV API_VERSION=${VERSION}

RUN mkdir -p /backend/data

# Runtime-only shared libs for source-compiled lxml (see builder stage) and Pillow (see
# ghunt-builder stage - GHunt depends on it, no prebuilt wheel yet for this image's Python 3.14),
# plus git - needed at runtime as a subprocess by the git_recon feature - and exiftool - needed
# at runtime as a subprocess by image_tools' exiftool_service for extended EXIF/IPTC/XMP/
# maker-note extraction, optional/best-effort if missing. No compilers/headers here: those stay
# in the builder/ghunt-builder stages.
RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache-runtime,sharing=locked \
    apt-get update && apt-get install -y \
    libxml2 \
    libxslt1.1 \
    liblzma5 \
    zlib1g \
    libjpeg62-turbo \
    git \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# subfinder/httpx (domain_finder's passive-subdomain-enumeration and live-host-probe
# panels), statically built in the go-tools-builder stage above - needed at runtime
# as subprocesses by subfinder_service.py/host_probe_service.py. The Go httpx binary
# is installed as `httpx-probe`, not `httpx`: the Python `httpx` package (already a
# dependency, requirements.in) registers its own `httpx` console-script in
# /opt/venv/bin, which is earlier on PATH than /usr/local/bin - installing under the
# same name would silently shell out to the wrong tool.
COPY --from=go-tools-builder /go/bin/subfinder /usr/local/bin/subfinder
COPY --from=go-tools-builder /go/bin/httpx /usr/local/bin/httpx-probe

# amass (active DNS brute-forcing / ASN-netblock discovery, the amass feature) +
# ae_isready (its readiness-check companion) - needed at runtime as subprocesses by
# amass_engine_service.py/amass_service.py. amass v5's `enum`/`subs` subcommands are
# HTTP clients to a separate `amass engine` process (SQLite-backed by default, no
# Postgres needed) that this app starts as a background subprocess at startup.
COPY --from=go-tools-builder /go/bin/amass /usr/local/bin/amass
COPY --from=go-tools-builder /go/bin/ae_isready /usr/local/bin/ae_isready

# GHunt (email_search's GHunt profile-lookup panel), isolated venv built above - needed at
# runtime as a subprocess by ghunt_profile_service.py. Not on PATH; called by absolute path.
COPY --from=ghunt-builder /opt/tools/ghunt /opt/tools/ghunt

# Non-root app user. `-m` gives it a real home dir, needed at runtime for
# maigret's site-database auto-update cache (~/.maigret) and, if headless
# email-search checks are enabled, pyppeteer's Chromium download
# (~/.local/share/pyppeteer) - both write under $HOME, not /backend/data.
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g appuser -s /usr/sbin/nologin appuser

# --chown here (instead of a separate `RUN chown -R`) avoids overlayfs
# copy-up duplicating the whole tree into another layer just to change
# ownership metadata.
COPY --chown=appuser:appuser ./ /backend/

EXPOSE 8000
ENTRYPOINT ["python3", "/backend/docker-entrypoint.py"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
