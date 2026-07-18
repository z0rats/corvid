FROM python:3.14-slim
WORKDIR /backend

RUN pip install --no-cache-dir uv

RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache,sharing=locked \
    apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libxml2-dev \
    libxslt-dev \
    liblzma-dev \
    zlib1g-dev \
    git

RUN mkdir -p /backend/data

# lxml has no prebuilt wheel for cp314 yet and must compile from source (~150s).
# Installed in its own layer, pinned to match requirements.txt, so unrelated
# requirements.txt changes don't invalidate this cache and force a rebuild.
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache \
    uv pip install --system "lxml[html-clean]==5.4.0"

COPY ./requirements.txt ./lxml-override.txt /backend/
# --override forces lxml==5.4.0 despite maigret's declared floor of lxml>=6.0.2
# (maigret doesn't actually use lxml directly; see lxml-override.txt).
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache \
    uv pip install --system --upgrade -r /backend/requirements.txt --override /backend/lxml-override.txt
COPY ./ /backend/

# Non-root app user. `-m` gives it a real home dir, needed at runtime for
# maigret's site-database auto-update cache (~/.maigret) and, if headless
# email-search checks are enabled, pyppeteer's Chromium download
# (~/.local/share/pyppeteer) - both write under $HOME, not /backend/data.
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g appuser -s /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /backend

EXPOSE 8000
ENTRYPOINT ["python3", "/backend/docker-entrypoint.py"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]