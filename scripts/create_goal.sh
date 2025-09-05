#!/usr/bin/env bash
set -euo pipefail
: "${BASE:=http://localhost:8000}"
: "${TOKEN:?Set TOKEN first, e.g. export TOKEN=$(scripts/mint_token.sh)}"
GOAL_NAME="${GOAL_NAME:-Emergency Fund}"
TARGET_AMOUNT="${TARGET_AMOUNT:-1000}"
TARGET_DATE="${TARGET_DATE:-2025-12-01}"
PRIORITY="${PRIORITY:-1}"

curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"name\":\"$GOAL_NAME\",\"target_amount\":$TARGET_AMOUNT,\"target_date\":\"$TARGET_DATE\",\"priority\":$PRIORITY}" \
  "$BASE/accounts/savings" >/dev/null && echo "Created goal: $GOAL_NAME"
