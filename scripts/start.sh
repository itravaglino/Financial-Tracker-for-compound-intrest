#!/usr/bin/env bash
# Build frontend and serve the full app with uvicorn (frontend + API).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

cd "$ROOT/frontend"
npm install
npm run build

cd "$ROOT/backend"
if [ ! -d venv ]; then
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install -r requirements.txt

export SECRET_KEY="${SECRET_KEY:-change-me-in-production}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./finance_tracker.db}"
export CORS_ORIGINS="${CORS_ORIGINS:-*}"
export PORT="${PORT:-8000}"

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
