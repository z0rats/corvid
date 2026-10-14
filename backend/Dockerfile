FROM ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21 AS uv

# subfinder/httpx/amass come from their upstream GitHub release archives rather than a
# `go install` from source: the releases ship static, stripped linux binaries for both
# arches this repo publishes (amd64/arm64), so this skips minutes of cold Go compilation.
# Each archive is pinned by exact tag + sha256 per arch (from the release's own
# checksums file) and the build fails on a mismatch. Bumping a tool means updating its
# version and both hashes together. Runs on the golang image only to avoid pinning one
# more base image - nothing here needs Go.
FROM golang:1.27-alpine@sha256:8a5910f31396cd4d89662f56c68b3ae31d374308270a1c3bd96672ee5ed43414 AS go-tools-fetch
ARG TARGETARCH
WORKDIR /dl
RUN set -eu; \
    case "$TARGETARCH" in \
      amd64) subfinder_sha=1b7f9c608e9a5bd59e609a5e09710d63c5485e92d3d49dc2c16eb4fdbe10cb60; \
             httpx_sha=9d8439e8b6c9aa7d1e2314817a392e00d5178da3af5652f7475f88868f418f76; \
             amass_sha=5e22b5f0239e7eb79439d60d43d3cd20dca2478588bc2242e91ab0c4f8fa40dd ;; \
      arm64) subfinder_sha=c81d49559c0f630177be9e347e502e7a3d474aacc6ff78291ffcb4964367d63d; \
             httpx_sha=fd7b123c1dfbc3d69f19f524e4eebcd6ec06b9a6cbd56813c76f11645197331e; \
             amass_sha=d05aace46ca5216f91226ffd23eeb4ce8ad2aa2548efe3a2bd59e81e6b0765b5 ;; \
      *) echo "unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac; \
    fetch() { wget -q -O "$1" "$2" && echo "$3  $1" | sha256sum -c -; }; \
    fetch subfinder.zip "https://github.com/projectdiscovery/subfinder/releases/download/v2.16.0/subfinder_2.16.0_linux_${TARGETARCH}.zip" "$subfinder_sha"; \
    fetch httpx.zip "https://github.com/projectdiscovery/httpx/releases/download/v1.12.0/httpx_1.12.0_linux_${TARGETARCH}.zip" "$httpx_sha"; \
    fetch amass.tar.gz "https://github.com/owasp-amass/amass/releases/download/v5.1.1/amass_linux_${TARGETARCH}.tar.gz" "$amass_sha"; \
    mkdir /out; \
    unzip -q -o subfinder.zip subfinder -d /out; \
    unzip -q -o httpx.zip httpx -d /out; \
    tar -xzf amass.tar.gz -C /out --strip-components=1 "amass_linux_${TARGETARCH}/amass"; \
    chmod 0755 /out/*

# ae_isready (amass's engine readiness check) isn't in amass's release archive, so it's
# still built from source at the same pinned tag. CGO_ENABLED=0 produces a fully static
# binary with no runtime dependency on this stage's (musl-based) libc, so it drops
# straight into the glibc-based runtime stage below; `-s -w` strips symbol/DWARF info
# (pure size), leaving module version info intact.
FROM golang:1.27-alpine@sha256:8a5910f31396cd4d89662f56c68b3ae31d374308270a1c3bd96672ee5ed43414 AS go-tools-builder
ENV CGO_ENABLED=0 GOBIN=/go/bin
RUN apk add --no-cache git ca-certificates
RUN --mount=type=cache,target=/root/.cache/go-build,id=go-build-cache \
    --mount=type=cache,target=/go/pkg/mod,id=go-mod-cache \
    go install -v -trimpath -ldflags="-s -w" github.com/owasp-amass/amass/v5/cmd/ae_isready@v5.1.1

# GHunt in its own isolated venv, not the main one below: `ghunt>=2.3.2` requires `rich<14`,
# which conflicts with the main venv's pinned `mitreattack-python==6.2.0` (-> `rich==15.0.0`) -
# see docs/adr/0018-isolated-tool-cli-venvs.md for the general pattern this formalizes. Called at
# runtime via its absolute path (`ghunt_config.GHUNT_BIN`), never through `PATH`, same reasoning
# as the Go `httpx`/`httpx-probe` rename above. The only stage that needs a C toolchain: GHunt
# pins `pillow<11`, which has no prebuilt wheel for this image's Python 3.14 and falls back to
# compiling from source. Bytecode precompiled for the same reason as the `builder` stage below.
# scipy/pywavelets (~120MB) are removed after install: they arrive only via `imagehash`, which
# imports them lazily inside phash()/whash(), and GHunt only calls average_hash()/
# hex_to_flathash() (numpy + Pillow). Re-check this if the ghunt pin is bumped.
FROM python:3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6 AS ghunt-builder
COPY --from=uv /uv /usr/local/bin/uv
RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache-ghunt-builder,sharing=locked \
    apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    zlib1g-dev \
    libjpeg-dev
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache-ghunt \
    uv venv /opt/tools/ghunt && \
    uv pip install --python /opt/tools/ghunt/bin/python ghunt==2.3.4 && \
    uv pip uninstall --python /opt/tools/ghunt/bin/python scipy pywavelets

FROM python:3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6 AS builder
WORKDIR /backend

COPY --from=uv /uv /usr/local/bin/uv

# No compiler toolchain here: every requirements.txt package ships a prebuilt
# cp314 wheel for amd64/arm64 (lxml/pillow bundle their own libxml2/libjpeg) or is
# pure Python. If a bump ever drops a wheel, the install fails loudly here rather
# than silently compiling - re-add build-essential + the -dev headers then.
#
# UV_COMPILE_BYTECODE: the runtime venv is root-owned and the app runs as appuser,
# so Python can't write __pycache__ next to the sources - without precompiled .pyc
# every container start recompiles every import (~4s of startup). Copy link mode
# since the uv cache is a separate mount, so hardlinks can't cross into the venv.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt /backend/
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache \
    uv pip install -r /backend/requirements.txt

FROM python:3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6
WORKDIR /backend

# Stamped from the release tag by CI (see .github/workflows/release.yml); falls
# back to this default for local builds and non-tagged CI images.
ARG VERSION=0.0.0-dev
ENV API_VERSION=${VERSION}

RUN mkdir -p /backend/data

# Runtime-only shared libs for GHunt's source-compiled Pillow (see ghunt-builder stage),
# plus git - needed at runtime as a subprocess by the git_recon feature - and exiftool - needed
# at runtime as a subprocess by image_tools' exiftool_service for extended EXIF/IPTC/XMP/
# maker-note extraction, optional/best-effort if missing. No compilers/headers here: those stay
# in the builder/ghunt-builder stages.
RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache-runtime,sharing=locked \
    apt-get update && apt-get install -y \
    zlib1g \
    libjpeg62-turbo \
    git \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# subfinder/httpx (domain_finder's passive-subdomain-enumeration and live-host-probe
# panels), static release binaries from the go-tools-fetch stage above - needed at runtime
# as subprocesses by subfinder_service.py/host_probe_service.py. The Go httpx binary
# is installed as `httpx-probe`, not `httpx`: the Python `httpx` package (already a
# dependency, requirements.in) registers its own `httpx` console-script in
# /opt/venv/bin, which is earlier on PATH than /usr/local/bin - installing under the
# same name would silently shell out to the wrong tool.
COPY --from=go-tools-fetch /out/subfinder /usr/local/bin/subfinder
COPY --from=go-tools-fetch /out/httpx /usr/local/bin/httpx-probe

# amass (active DNS brute-forcing / ASN-netblock discovery, the amass feature) +
# ae_isready (its readiness-check companion) - needed at runtime as subprocesses by
# amass_engine_service.py/amass_service.py. amass v5's `enum`/`subs` subcommands are
# HTTP clients to a separate `amass engine` process (SQLite-backed by default, no
# Postgres needed) that this app starts as a background subprocess at startup.
COPY --from=go-tools-fetch /out/amass /usr/local/bin/amass
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

# Lets update.sh prune superseded Corvid images without touching the host's other images.
LABEL org.opencontainers.image.source="https://github.com/z0rats/corvid"
EXPOSE 8000
ENTRYPOINT ["python3", "/backend/docker-entrypoint.py"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
