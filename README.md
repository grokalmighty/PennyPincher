# PennyPincher
Personal finance management


// To run in root

Terminal 1:

cd ~/PennyPincher
./scripts/start_api.sh

Terminal 2:

cd ~/PennyPincher
export BASE="http://localhost:8000"
export MONTH="2025-08"
export CAP="2500"

# get a token
export TOKEN=$(./scripts/mint_token.sh)

# optional: seed + goal (run once)
./scripts/seed_july.sh
./scripts/seed_cpi_aug.sh
./scripts/create_goal.sh

# run the narrated demo
./scripts/pinch_live_demo.sh
# or the one-button flow:
./scripts/demo_all.sh

# Video link:
# https://drive.google.com/file/d/18e8EPoI0wIyZ2j8pDrZEJkKxomexUKeN/view?usp=drive_link