#!/bin/sh
set -e

echo "[INIT] Applying database migrations (alembic upgrade head)..."
alembic upgrade head

echo "[INIT] Starting application server..."
exec "$@"
