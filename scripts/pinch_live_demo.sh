#!/usr/bin/env bash
set -euo pipefail
: "${BASE:=http://localhost:8000}"
: "${MONTH:=2025-08}"
: "${CAP:=2500}"
: "${TOKEN:=$(scripts/mint_token.sh)}"

HAVE_JQ=0; command -v jq >/dev/null && HAVE_JQ=1
say(){ printf "\n\033[1m%s\033[0m\n" "$*"; }

say "Pinch: one high-leverage money move per month — LIVE DEMO"

say "1) Coach Insight (one actionable nudge + $ impact)"
if [ "$HAVE_JQ" -eq 1 ]; then
  curl -s -H "Authorization: Bearer $TOKEN" "$BASE/coach/insights/$MONTH" \
  | jq -r '.insights[] | "• \(.title)\n  impact: $ \(.impact_estimate_monthly)\n  \(.body)\n  why: EMA=\(.source_ref.inputs.baseline_ema) z=\(.source_ref.inputs.z_score) recurring=\(.source_ref.inputs.recurring_coverage)"'
else
  curl -s -H "Authorization: Bearer $TOKEN" "$BASE/coach/insights/$MONTH" | python -m json.tool
fi

say "2) Forecast vs Actual (personal EMA + z-score + recurring coverage)"
if [ "$HAVE_JQ" -eq 1 ]; then
  curl -s -H "Authorization: Bearer $TOKEN" "$BASE/forecast/table?month=$MONTH" \
  | jq -r '.[0:5] | .[] | "\(.category): actual $" + (.actual_spent|tostring) + " vs forecast $" + (.forecast|tostring) + " | EMA $" + (.baseline_ema|tostring) + " | z=" + (.z_score|tostring) + " | recurring=" + ((.recurring_coverage*100|floor|tostring) + "%") + (if .anomaly then " | ANOMALY" else "" end)'
else
  curl -s -H "Authorization: Bearer $TOKEN" "$BASE/forecast/table?month=$MONTH" | python -m json.tool
fi

say "3) Goal Forecast (P50/P80) — with a realistic monthly savings override"
MS=${MS:-150}
if [ "$HAVE_JQ" -eq 1 ]; then
  curl -s -H "Authorization: Bearer $TOKEN" "$BASE/goals/forecast?month=$MONTH&spend_cap=$CAP&monthly_savings_override=$MS" \
  | jq -r '"planned monthly $" + (.monthly_savings|tostring) + "\n" +
           ( if (.goals|length)>0
             then ( .goals[0] | "• " + .name + ": $" + (.current|tostring) + " / $" + (.target|tostring) +
                    " | P50 " + (.projected_date_p50 // "—") + " | P80 " + (.projected_date_p80 // "—") )
             else "• No active goals — create one via POST /accounts/savings"
             end )'
else
  curl -s -H "Authorization: Bearer $TOKEN" "$BASE/goals/forecast?month=$MONTH&spend_cap=$CAP&monthly_savings_override=$MS" | python -m json.tool
fi

say "Done — Hybrid AI: personal EMA + cadence-aware dampening + small adaptive policy for the one-card coach."
