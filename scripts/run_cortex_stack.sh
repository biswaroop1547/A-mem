#!/usr/bin/env bash
set -euo pipefail

# Run Cortex stack (Chroma + Postgres + API) in a non-systemd environment.
# Intended for minimal/container-like hosts.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/api"

export CHROMA_HOST="${CHROMA_HOST:-127.0.0.1}"
export CHROMA_PORT="${CHROMA_PORT:-7003}"
export CHROMA_URI="${CHROMA_URI:-http://$CHROMA_HOST:$CHROMA_PORT}"

export API_HOST="${API_HOST:-127.0.0.1}"
export API_PORT="${API_PORT:-7001}"

export PG_HOST="${PG_HOST:-127.0.0.1}"
export PG_PORT="${PG_PORT:-5432}"
export PG_USER="${PG_USER:-postgres}"
export PG_PASSWORD="${PG_PASSWORD:-postgres}"
export PG_DB="${PG_DB:-cortex_api}"
export DATABASE_URL="${DATABASE_URL:-postgresql://$PG_USER:$PG_PASSWORD@$PG_HOST:$PG_PORT/$PG_DB}"

# OpenRouter support (optional): use OPENROUTER_API_KEY with OpenAI-compatible base_url.
if [[ -n "${OPENROUTER_API_KEY:-}" && -z "${OPENAI_API_KEY:-}" ]]; then
  export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://openrouter.ai/api/v1}"
fi

mkdir -p "$ROOT_DIR/logs"

log(){ echo "[cortex-stack] $*"; }

# Ensure Chroma running
if ! curl -fsS "$CHROMA_URI/api/v1/heartbeat" >/dev/null 2>&1; then
  log "Starting Chroma on $CHROMA_HOST:$CHROMA_PORT"
  (cd "$ROOT_DIR" && "$ROOT_DIR/.venv/bin/chroma" run --host "$CHROMA_HOST" --port "$CHROMA_PORT") \
    >"$ROOT_DIR/logs/chroma.log" 2>&1 &
  sleep 1
fi

# Ensure Postgres running
if ! pg_isready -h "$PG_HOST" -p "$PG_PORT" >/dev/null 2>&1; then
  log "Starting Postgres cluster 14/main"
  pg_ctlcluster 14 main start >/dev/null 2>&1 || true
  sleep 1
fi

# Ensure DB exists
if ! su - postgres -c "psql -tAc 'SELECT 1 FROM pg_database WHERE datname=\"$PG_DB\"'" | grep -q 1; then
  log "Creating DB $PG_DB"
  su - postgres -c "psql -c 'CREATE DATABASE $PG_DB;'" >/dev/null
fi

log "Starting API on $API_HOST:$API_PORT"
cd "$API_DIR"
exec "$ROOT_DIR/.venv/bin/uvicorn" app.main:app --host "$API_HOST" --port "$API_PORT"
