# Cloudflare Containers Dockerfile for Banana Slides Python Backend
# Build context must be repository root (configured via image_build_context: ".." in wrangler.jsonc)

FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:3.10-slim

WORKDIR /app

ARG TIGRISFS_VERSION=1.2.1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    ffmpeg \
    fonts-noto-cjk \
    fuse3 \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

# Install tigrisfs for optional Cloudflare R2 FUSE mount (/app/uploads)
RUN ARCH="$(dpkg --print-architecture)" && \
    case "$ARCH" in \
      amd64|x86_64) TIGRIS_ARCH=amd64 ;; \
      arm64|aarch64) TIGRIS_ARCH=arm64 ;; \
      *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;; \
    esac && \
    curl -fL "https://github.com/tigrisdata/tigrisfs/releases/download/v${TIGRISFS_VERSION}/tigrisfs_${TIGRISFS_VERSION}_linux_${TIGRIS_ARCH}.tar.gz" -o /tmp/tigrisfs.tar.gz && \
    tar -xzf /tmp/tigrisfs.tar.gz -C /usr/local/bin/ && \
    rm -f /tmp/tigrisfs.tar.gz && \
    chmod +x /usr/local/bin/tigrisfs

COPY --from=uv /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
ENV UV_HTTP_TIMEOUT=300
RUN uv sync --frozen --no-install-project

COPY backend/ ./backend/
COPY assets/ ./assets/
COPY cloudflare-backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && mkdir -p /app/backend/instance /app/uploads

ENV PYTHONPATH=/app
ENV FLASK_APP=backend/app.py
ENV IN_DOCKER=1
ENV PYTHONUNBUFFERED=1
ENV UPLOAD_FOLDER=/app/uploads

EXPOSE 5000

CMD ["/app/entrypoint.sh"]
