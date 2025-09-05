#!/usr/bin/env bash
set -euo pipefail
# Run the API server (keep this in Terminal 1)
# Optional env: PORT (default 8000), DATABASE_URL, JWT_SECRET
cd "$(dirname "$0")/.."/backend
export JWT_SECRET="${JWT_SECRET:-devsecret}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./demo.db}"
uvicorn app.main:app --reload --port "${PORT:-8000}"
