"""Clean the raw data with pandas and load it into a SQLite database (data/retail.db)."""
import sqlite3, pandas as pd
cust = pd.read_csv("data/raw/customers.csv"); prod = pd.read_csv("data/raw/products.csv")
orders = pd.read_csv("data/raw/orders.csv"); items = pd.read_csv("data/raw/order_items.csv")
log = {}

cust["city"] = cust["city"].str.strip().str.title()
n = len(orders); orders = orders.drop_duplicates(); log["duplicate orders removed"] = n - len(orders)
n = len(orders); orders = orders.dropna(subset=["customer_id"]); log["orders without customer removed"] = n - len(orders)
orders["customer_id"] = orders["customer_id"].astype(int)
n = len(orders); orders = orders[pd.to_datetime(orders["order_date"]) <= "2025-12-31"]; log["future-dated orders removed"] = n - len(orders)
n = len(items); items = items[items["quantity"] > 0]; log["negative-quantity items removed"] = n - len(items)
n = len(items); items = items[items["product_id"].isin(prod["product_id"])]; log["orphan product items removed"] = n - len(items)
n = len(items); items = items[items["order_id"].isin(orders["order_id"])]; log["items of removed orders removed"] = n - len(items)

con = sqlite3.connect("data/retail.db")
for name, df in [("customers", cust), ("products", prod), ("orders", orders), ("order_items", items)]:
    df.to_sql(name, con, if_exists="replace", index=False)
    df.to_csv(f"data/clean/{name}.csv", index=False)
con.close()
pd.Series(log, name="records").to_csv("reports/cleaning_log.csv")
print(pd.Series(log, name="records").to_string())
print("clean rows:", len(cust), len(prod), len(orders), len(items))
