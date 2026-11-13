"""Data quality checks on the raw CSV files. Writes reports/data_quality_report.csv"""
import pandas as pd
cust = pd.read_csv("data/raw/customers.csv"); prod = pd.read_csv("data/raw/products.csv")
orders = pd.read_csv("data/raw/orders.csv"); items = pd.read_csv("data/raw/order_items.csv")

checks = []
def add(table, issue, count): checks.append({"table": table, "issue": issue, "records_affected": int(count)})

add("orders", "duplicate order rows", orders.duplicated().sum())
add("orders", "missing customer_id", orders["customer_id"].isna().sum())
add("orders", "order_date in the future (after 2025-12-31)", (pd.to_datetime(orders["order_date"]) > "2025-12-31").sum())
add("order_items", "negative quantity", (items["quantity"] <= 0).sum())
add("order_items", "product_id not found in products (orphan)", (~items["product_id"].isin(prod["product_id"])).sum())
add("customers", "inconsistent city text (case or spaces)", (cust["city"] != cust["city"].str.strip().str.title()).sum())
add("customers", "missing values (any column)", cust.isna().any(axis=1).sum())
add("products", "price <= 0", (prod["price"] <= 0).sum())

rep = pd.DataFrame(checks)
rep.to_csv("reports/data_quality_report.csv", index=False)
print(rep.to_string(index=False))
