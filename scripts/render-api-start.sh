#!/bin/sh
set -e
PORT="${PORT:-8000}"
WORKERS="${UVICORN_WORKERS:-1}"
exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --workers "$WORKERS"
