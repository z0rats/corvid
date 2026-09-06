FROM ghcr.io/astral-sh/uv:0.12.7@sha256:95f2aa1fe59274951cfe9b0cbc7972e879ff1004bc8945d130a32eb0dbd85945 AS uv

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

# Runtime-only shared libs for source-compiled lxml (see builder stage), plus
# git - needed at runtime as a subprocess by the git_recon feature - and
# exiftool - needed at runtime as a subprocess by image_tools' exiftool_service
# for extended EXIF/IPTC/XMP/maker-note extraction, optional/best-effort if
# missing. No compilers/headers here: those stay in the builder stage.
RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache-runtime,sharing=locked \
    apt-get update && apt-get install -y \
    libxml2 \
    libxslt1.1 \
    liblzma5 \
    zlib1g \
    git \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

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
