"""Create a reproducible SYNTHETIC retail dataset (seed=42) with realistic errors injected.
The data is simulated for practice; it is not real company data."""
import numpy as np, pandas as pd
rng = np.random.default_rng(42)

cities = ["Dhaka", "Chattogram", "Sylhet", "Rajshahi", "Khulna"]
city_p = [0.38, 0.22, 0.14, 0.14, 0.12]
cust = pd.DataFrame({
    "customer_id": range(1, 501),
    "customer_name": [f"Customer {i:03d}" for i in range(1, 501)],
    "city": rng.choice(cities, 500, p=city_p),
    "segment": rng.choice(["Regular", "Premium", "New"], 500, p=[0.6, 0.15, 0.25]),
    "signup_date": pd.to_datetime("2023-01-01") + pd.to_timedelta(rng.integers(0, 900, 500), unit="D"),
})

cats = {"Electronics": (4500, 60000), "Fashion": (600, 6000), "Grocery": (80, 1500), "Home": (500, 15000), "Books": (150, 1200)}
rows, pid = [], 1
for cat, (lo, hi) in cats.items():
    for k in range(8):
        rows.append((pid, f"{cat} Item {k+1}", cat, int(rng.integers(lo, hi))))
        pid += 1
prod = pd.DataFrame(rows, columns=["product_id", "product_name", "category", "price"])

n_orders = 5000
dates = pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, n_orders), unit="D")
# more orders in Nov/Dec (festival season)
boost = rng.random(n_orders) < 0.18
dates = pd.Series(dates)
dates[boost] = pd.to_datetime("2025-11-01") + pd.to_timedelta(rng.integers(0, 60, boost.sum()), unit="D")
orders = pd.DataFrame({
    "order_id": range(1001, 1001 + n_orders),
    "customer_id": rng.choice(cust.customer_id, n_orders),
    "order_date": dates.dt.strftime("%Y-%m-%d"),
    "status": rng.choice(["Delivered", "Cancelled", "Returned", "Pending"], n_orders, p=[0.78, 0.09, 0.06, 0.07]),
    "payment_method": rng.choice(["Card", "bKash", "Cash on Delivery", "Nagad"], n_orders, p=[0.25, 0.32, 0.30, 0.13]),
})
items = []
for oid in orders.order_id:
    for p in rng.choice(prod.product_id, int(rng.integers(1, 5)), replace=False):
        price = int(prod.loc[prod.product_id == p, "price"].iloc[0])
        disc = rng.choice([1.0, 0.95, 0.9, 0.8], p=[0.7, 0.12, 0.12, 0.06])
        items.append((oid, int(p), int(rng.integers(1, 5)), round(price * disc, 2)))
items = pd.DataFrame(items, columns=["order_id", "product_id", "quantity", "unit_price"])

# ---------- inject known data-quality problems (so the checks have something to find) ----------
cust["city"] = cust["city"].astype(object)
idx = rng.choice(cust.index, 60, replace=False)
cust.loc[idx[:25], "city"] = cust.loc[idx[:25], "city"].str.upper()          # DHAKA
cust.loc[idx[25:45], "city"] = cust.loc[idx[25:45], "city"] + " "            # trailing space
cust.loc[idx[45:], "city"] = cust.loc[idx[45:], "city"].str.lower()          # dhaka
orders.loc[rng.choice(orders.index, 30, replace=False), "customer_id"] = np.nan   # missing customer
bad = rng.choice(orders.index, 15, replace=False)
orders.loc[bad, "order_date"] = "2026-" + orders.loc[bad, "order_date"].str[5:]      # future dates
orders = pd.concat([orders, orders.sample(40, random_state=1)], ignore_index=True)   # 40 duplicate orders
items.loc[rng.choice(items.index, 30, replace=False), "quantity"] *= -1              # negative quantity
items.loc[rng.choice(items.index, 20, replace=False), "product_id"] = 999            # orphan product

cust.to_csv("data/raw/customers.csv", index=False)
prod.to_csv("data/raw/products.csv", index=False)
orders.to_csv("data/raw/orders.csv", index=False)
items.to_csv("data/raw/order_items.csv", index=False)
print("raw rows:", len(cust), len(prod), len(orders), len(items))
