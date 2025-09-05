#!/usr/bin/env bash
set -euo pipefail
: "${BASE:=http://localhost:8000}"
: "${TOKEN:?Set TOKEN first, e.g. export TOKEN=$(scripts/mint_token.sh)}"

cat > /tmp/demo_transactions_july.csv << 'CSV'
date,amount,currency,merchant_alias,preset_category,account_alias,issuer,network,last4
2025-07-01,-1200.00,USD,RENTAL CO,housing_rent,CHK-001,Chase,Visa,1234
2025-07-03,-14.50,USD,STARBUCKS,food_drink:coffee,CHK-001,Chase,Visa,1234
2025-07-05,-60.00,USD,GROCER MART,groceries,CHK-001,Chase,Visa,1234
2025-07-10,-49.99,USD,NETSTREAM,internet,CHK-001,Chase,Visa,1234
2025-07-14,-30.00,USD,UBER *TRIP,transport,CHK-001,Chase,Visa,1234
2025-07-21,-50.00,USD,GROCER MART,groceries,CHK-001,Chase,Visa,1234
2025-07-28,-49.99,USD,NETSTREAM,internet,CHK-001,Chase,Visa,1234
2025-07-29,-60.00,USD,UBER *TRIP,transport,CHK-001,Chase,Visa,1234
CSV

curl -s -H "Authorization: Bearer $TOKEN" -F "file=@/tmp/demo_transactions_july.csv" \
  "$BASE/transactions/upload" >/dev/null && echo "Seeded July transactions."
