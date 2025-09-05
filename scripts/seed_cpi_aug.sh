#!/usr/bin/env bash
set -euo pipefail
: "${BASE:=http://localhost:8000}"
: "${TOKEN:?Set TOKEN first, e.g. export TOKEN=$(scripts/mint_token.sh)}"

cat > /tmp/demo_cpi.csv << 'CSV'
month,category,yoy
2025-08,groceries,0.03
2025-08,transport,0.01
2025-08,internet,0.00
2025-08,housing_rent,0.02
2025-08,food_drink:coffee,0.04
CSV

cat > /tmp/demo_transactions_aug.csv << 'CSV'
date,amount,currency,merchant_alias,preset_category,account_alias,issuer,network,last4
2025-08-01,-1200.00,USD,RENTAL CO,housing_rent,CHK-001,Chase,Visa,1234
2025-08-02,-65.25,USD,GROCER MART,groceries,CHK-001,Chase,Visa,1234
2025-08-03,-14.50,USD,STARBUCKS,food_drink:coffee,CHK-001,Chase,Visa,1234
2025-08-04,-22.00,USD,UBER *TRIP,transport,CHK-001,Chase,Visa,1234
2025-08-05,-55.70,USD,GROCER MART,groceries,CHK-001,Chase,Visa,1234
2025-08-07,-65.25,USD,GROCER MART,groceries,CHK-001,Chase,Visa,1234
2025-08-10,-49.99,USD,NETSTREAM,internet,CHK-001,Chase,Visa,1234
2025-08-15,-14.50,USD,STARBUCKS,food_drink:coffee,CHK-001,Chase,Visa,1234
2025-08-21,-65.25,USD,GROCER MART,groceries,CHK-001,Chase,Visa,1234
2025-08-28,-49.99,USD,NETSTREAM,internet,CHK-001,Chase,Visa,1234
2025-08-29,-220.00,USD,UBER *TRIP,transport,CHK-001,Chase,Visa,1234
CSV

curl -s -H "Authorization: Bearer $TOKEN" -F "file=@/tmp/demo_cpi.csv" "$BASE/cpi/upload" >/dev/null \
  && echo "Uploaded CPI."
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@/tmp/demo_transactions_aug.csv" "$BASE/transactions/upload" >/dev/null \
  && echo "Uploaded August transactions."
