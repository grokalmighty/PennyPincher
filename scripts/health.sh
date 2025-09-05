#!/usr/bin/env bash
set -euo pipefail
: "${BASE:=http://localhost:8000}"
: "${TOKEN:?Set TOKEN first}"
echo "GET $BASE/healthz"
curl -s -i -H "Authorization: Bearer $TOKEN" "$BASE/healthz" | sed -n '1,5p'
