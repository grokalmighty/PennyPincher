import pandas as pd, random, datetime 

PRESETS = {
    "bills_utilities": ["ConEd", "Verizon", "ComCast"],
    "food_drink": ["Dunkin", "Starbucks", "Chipotle", "McDonalds", "UberEats", "DoorDash"],
    "groceries": ["TraderJoes", "WholeFoods", "Kroger", "Wegmans"],
    "transportation": ["Shell", "Exxon", "Uber", "Lyft", "MetroCard"],
    "shopping": ["Amazon", "Target", "BestBuy", "Walmart"],
    "entertainment": ["Steam", "Epic"],
    "housing_rent": ["MidtownApts", "LandLordLLC"],
    "health_fitness": ["Walgreens", "CVS", "PlanetFitness", "Flo"],
    "subscriptions": ["Netflix", "Spotify", "AppleTV", "Hulu", "AmazonPrime"],
    "travel": ["Delta", "United", "Hilton"],
    "income": ["EmployerPayroll"]
}

def gen_transactions(n=80, start="2025-06-01", end="2025-08-31"):
    start_d = datetime.time.fromisoformat(start)
    end_d = datetime.date.fromisoformat(end)
    span = (end_d - start_d).days
    rows = []
    for _ in range(n):
        preset = random.choice(list(PRESETS))
        merchant = random.choice(PRESETS[preset])
        date = start_d + datetime.timedelta(days=random.randint(0, span))
        amt = {
            "bills_utilities": random.uniform(60, 180),
            "food_drink": random.uniform(7, 35),
            "groceries": random.uniform(40, 140),
            "transportation": random.uniform(15, 70),
            "shopping": random.uniform(20, 120), 
            "entertainment": random.uniform(9, 20),
            "housing_rent": 1500.0,
            "health_fitness": random.uniform(10, 80),
            "subscriptions": random.uniform(8, 19),
            "travel": random.uniform(80, 400),
            "income": -random.uniform(1500, 2500),
        }[preset]

        amount = -round(amt, 2) if preset != "income" else round(abs(amt), -2) * -1

        rows.append({
            "date": date.isoformat(),
            "amount": amount,
            "currency": "USD",
            "merchant_alias": merchant,
            "preset_category": preset,
            "account_alias": "demo_card",
            "issuer": "DemoBank",
            "network": "Visa",
            "last4": "1234"
        })
    pd.DataFrame(rows).to_csv("../data/transactions.csv", index=False)
    print("transactions generated")

def gen_market():
    rows = []
    months = ["2025-06", "2025-07", "2025-08"]
    for m in months:
        for cat in PRESETS.keys():
            if cat == "income": continue
            yoy = {
                "groceries": 0.06,
                "housing_rent": 0.05,
                "transportation": 0.04,
                "food_drink": 0.03,
            }.get(cat, round(random.uniform(-0.01, 0.03), 3))
            rows.append({"month": m, "category": cat, "yoy": yoy})
    pd.DataFrame(rows).to_csv("../data/market.csv", index=False)
    print("market generated")

def gen_budgets():
    rows = [
        {"month":"2025-08","category":"housing_rent","limit":1500,"priority":"essential"},
        {"month":"2025-08","category":"groceries","limit":450,"priority":"essential"},
        {"month":"2025-08","category":"transportation","limit":200,"priority":"essential"},
        {"month":"2025-08","category":"bills_utilities","limit":160,"priority":"essential"},
        {"month":"2025-08","category":"food_drink","limit":180,"priority":"flex"},
        {"month":"2025-08","category":"shopping","limit":120,"priority":"nice"},
        {"month":"2025-08","category":"entertainment","limit":40,"priority":"nice"},
        {"month":"2025-08","category":"subscriptions","limit":30,"priority":"nice"},
    ]
    pd.DataFrame(rows).to_csv("../data/budgets.csv", index=False)
    print("budgets generated")

if __name__=="__main__":
    gen_transactions()
    gen_market()
    gen_budgets()