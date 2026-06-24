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
    zlib1g-dev

RUN mkdir -p /backend/data

# lxml has no prebuilt wheel for cp314 yet and must compile from source (~150s).
# Installed in its own layer, pinned to match requirements.txt, so unrelated
# requirements.txt changes don't invalidate this cache and force a rebuild.
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache \
    uv pip install --system "lxml[html-clean]==5.4.0"

COPY ./requirements.txt /backend/requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache \
    uv pip install --system --upgrade -r /backend/requirements.txt
COPY ./ /backend/
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]