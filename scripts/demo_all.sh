#!/usr/bin/env bash
set -euo pipefail
export BASE="${BASE:-http://localhost:8000}"
export MONTH="${MONTH:-2025-08}"
export CAP="${CAP:-2500}"

# Mint token & export to current shell
export TOKEN="$(scripts/mint_token.sh)"
echo "TOKEN minted."

# Optional seeds (idempotent for demo)
scripts/seed_july.sh || true
scripts/seed_cpi_aug.sh || true
scripts/create_goal.sh || true

# Run the narrated demo
scripts/pinch_live_demo.sh
