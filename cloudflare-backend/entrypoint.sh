#!/bin/sh
set -eu

UPLOAD_DIR="${UPLOAD_FOLDER:-/app/uploads}"
mkdir -p "$UPLOAD_DIR" /app/backend/instance

R2_MOUNTED=0
FUSE_PID=""
APP_PID=""

cleanup() {
  if [ -n "$APP_PID" ] && kill -0 "$APP_PID" 2>/dev/null; then
    kill -TERM "$APP_PID" 2>/dev/null || true
    wait "$APP_PID" 2>/dev/null || true
  fi
  if [ "$R2_MOUNTED" -eq 1 ]; then
    fusermount3 -u "$UPLOAD_DIR" 2>/dev/null || umount "$UPLOAD_DIR" 2>/dev/null || true
  fi
  if [ -n "$FUSE_PID" ] && kill -0 "$FUSE_PID" 2>/dev/null; then
    kill -TERM "$FUSE_PID" 2>/dev/null || true
    wait "$FUSE_PID" 2>/dev/null || true
  fi
}

if [ -n "${R2_ACCOUNT_ID:-}" ] && [ -n "${R2_BUCKET_NAME:-}" ] && [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ -n "${AWS_SECRET_ACCESS_KEY:-}" ]; then
  R2_ENDPOINT="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
  export AWS_REGION="${AWS_REGION:-auto}"

  /usr/local/bin/tigrisfs \
    --endpoint "$R2_ENDPOINT" \
    --region auto \
    -f "$R2_BUCKET_NAME" "$UPLOAD_DIR" &
  FUSE_PID=$!
  trap cleanup EXIT INT TERM

  attempt=0
  until mountpoint -q "$UPLOAD_DIR"; do
    if ! kill -0 "$FUSE_PID" 2>/dev/null; then
      echo "Error: tigrisfs exited before mounting $UPLOAD_DIR" >&2
      exit 1
    fi
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 30 ]; then
      echo "Error: timed out waiting for R2 FUSE mount at $UPLOAD_DIR" >&2
      exit 1
    fi
    sleep 1
  done
  R2_MOUNTED=1
  echo "Mounted Cloudflare R2 bucket '$R2_BUCKET_NAME' at $UPLOAD_DIR"
else
  echo "R2 credentials not fully configured; using ephemeral local disk at $UPLOAD_DIR" >&2
fi

cd /app/backend
/app/.venv/bin/alembic upgrade head

if [ "$R2_MOUNTED" -eq 1 ]; then
  /app/.venv/bin/python app.py &
  APP_PID=$!
  wait "$APP_PID"
else
  exec /app/.venv/bin/python app.py
fi
