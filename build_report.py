"""Build the Excel report (formulas, native charts, pivot-style table) and PNG charts from the SQL results."""
import sqlite3, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "reports/sql_results/"
monthly = pd.read_csv(R + "Q1.csv"); cat = pd.read_csv(R + "Q2.csv"); top = pd.read_csv(R + "Q3.csv")
city = pd.read_csv(R + "Q5.csv"); pay = pd.read_csv(R + "Q6.csv"); prods = pd.read_csv(R + "Q7.csv")
dq = pd.read_csv("reports/data_quality_report.csv"); clog = pd.read_csv("reports/cleaning_log.csv", index_col=0).iloc[:, 0]

con = sqlite3.connect("data/retail.db")
pivot = pd.read_sql_query("""SELECT c.city, p.category, SUM(oi.quantity*oi.unit_price) AS revenue
  FROM orders o JOIN customers c ON c.customer_id=o.customer_id
  JOIN order_items oi ON oi.order_id=o.order_id JOIN products p ON p.product_id=oi.product_id
  WHERE o.status='Delivered' GROUP BY c.city, p.category""", con)
pv = pivot.pivot_table(index="city", columns="category", values="revenue", aggfunc="sum", margins=True, margins_name="Total").round(0)

# ---------------- Excel ----------------
with pd.ExcelWriter("reports/retail_sales_report.xlsx", engine="xlsxwriter") as xw:
    wb = xw.book
    h = wb.add_format({"bold": True, "bg_color": "#1F3A5F", "font_color": "white", "border": 1})
    money = wb.add_format({"num_format": "#,##0"}); big = wb.add_format({"bold": True, "font_size": 14, "num_format": "#,##0"})
    lab = wb.add_format({"bold": True})

    ws = wb.add_worksheet("Summary"); xw.sheets["Summary"] = ws
    monthly.to_excel(xw, sheet_name="Monthly Revenue", index=False); wm = xw.sheets["Monthly Revenue"]
    n = len(monthly)
    for i, c in enumerate(monthly.columns): wm.write(0, i, c, h)
    wm.set_column(0, 0, 12); wm.set_column(1, 2, 16, money)
    ch = wb.add_chart({"type": "line"})
    ch.add_series({"name": "Revenue", "categories": f"='Monthly Revenue'!$A$2:$A${n+1}", "values": f"='Monthly Revenue'!$C$2:$C${n+1}"})
    ch.set_title({"name": "Monthly revenue (delivered orders)"}); ch.set_legend({"none": True}); ch.set_size({"width": 640, "height": 320})
    wm.insert_chart("E2", ch)

    cat.to_excel(xw, sheet_name="Category", index=False); wc = xw.sheets["Category"]
    for i, c in enumerate(cat.columns): wc.write(0, i, c, h)
    wc.set_column(0, 0, 14); wc.set_column(1, 2, 16, money)
    cc = wb.add_chart({"type": "column"})
    cc.add_series({"name": "Revenue", "categories": f"=Category!$A$2:$A${len(cat)+1}", "values": f"=Category!$C$2:$C${len(cat)+1}"})
    cc.set_title({"name": "Revenue by category"}); cc.set_legend({"none": True}); wc.insert_chart("E2", cc)

    city.to_excel(xw, sheet_name="City", index=False); wy = xw.sheets["City"]
    for i, c in enumerate(city.columns): wy.write(0, i, c, h)
    wy.set_column(0, 0, 14); wy.set_column(1, 3, 16, money)
    top.to_excel(xw, sheet_name="Top Customers", index=False); wt = xw.sheets["Top Customers"]
    for i, c in enumerate(top.columns): wt.write(0, i, c, h)
    wt.set_column(0, 4, 16)
    prods.to_excel(xw, sheet_name="Top Products", index=False); wp = xw.sheets["Top Products"]
    for i, c in enumerate(prods.columns): wp.write(0, i, c, h)
    wp.set_column(0, 3, 18)
    pay.to_excel(xw, sheet_name="Payment Methods", index=False); wpm = xw.sheets["Payment Methods"]
    for i, c in enumerate(pay.columns): wpm.write(0, i, c, h)
    wpm.set_column(0, 4, 20)
    pv.to_excel(xw, sheet_name="City x Category"); wv = xw.sheets["City x Category"]; wv.set_column(0, 6, 15, money)
    dq.to_excel(xw, sheet_name="Data Quality", index=False); wd = xw.sheets["Data Quality"]
    for i, c in enumerate(dq.columns): wd.write(0, i, c, h)
    wd.set_column(0, 0, 14); wd.set_column(1, 1, 48); wd.set_column(2, 2, 18)

    # Summary sheet uses live Excel formulas that point at the Monthly Revenue sheet
    ws.set_column(0, 0, 34); ws.set_column(1, 1, 20)
    ws.write(0, 0, "Retail Sales Report - 2025 (synthetic data)", wb.add_format({"bold": True, "font_size": 16}))
    rev = monthly["revenue"]; orders_total = int(monthly["orders"].sum())
    ws.write(2, 0, "Total revenue (delivered)", lab); ws.write_formula(2, 1, f"=SUM('Monthly Revenue'!C2:C{n+1})", big, rev.sum())
    ws.write(3, 0, "Delivered orders", lab);          ws.write_formula(3, 1, f"=SUM('Monthly Revenue'!B2:B{n+1})", big, orders_total)
    ws.write(4, 0, "Average monthly revenue", lab);   ws.write_formula(4, 1, f"=AVERAGE('Monthly Revenue'!C2:C{n+1})", big, rev.mean())
    ws.write(5, 0, "Average order value", lab);       ws.write_formula(5, 1, "=B3/B4", big, rev.sum() / orders_total)
    best = monthly.loc[rev.idxmax()]
    ws.write(6, 0, "Best month", lab); ws.write_formula(6, 1, f"=INDEX('Monthly Revenue'!A2:A{n+1},MATCH(MAX('Monthly Revenue'!C2:C{n+1}),'Monthly Revenue'!C2:C{n+1},0))", big, best["month"])
    ws.write(7, 0, "Best month revenue", lab); ws.write_formula(7, 1, f"=MAX('Monthly Revenue'!C2:C{n+1})", big, rev.max())

# ---------------- PNG charts ----------------
navy = "#1F3A5F"
fig, ax = plt.subplots(figsize=(8, 3.6)); ax.plot(monthly["month"], monthly["revenue"] / 1e6, marker="o", color=navy)
ax.set_title("Monthly revenue (delivered orders)"); ax.set_ylabel("Revenue (million BDT)"); ax.grid(alpha=.3); plt.xticks(rotation=45)
plt.tight_layout(); plt.savefig("charts/monthly_revenue.png", dpi=150); plt.close()
fig, ax = plt.subplots(figsize=(6, 3.6)); ax.bar(cat["category"], cat["revenue"] / 1e6, color=navy)
ax.set_title("Revenue by category"); ax.set_ylabel("Revenue (million BDT)"); plt.tight_layout(); plt.savefig("charts/category_revenue.png", dpi=150); plt.close()
fig, ax = plt.subplots(figsize=(6, 3.6)); ax.bar(city["city"], city["avg_order_value"], color=navy)
ax.set_title("Average order value by city"); ax.set_ylabel("BDT"); plt.tight_layout(); plt.savefig("charts/city_aov.png", dpi=150); plt.close()

# ---------------- findings from the real output ----------------
tot = rev.sum(); top_cat = cat.iloc[0]; share = 100 * top_cat["revenue"] / tot
lo = monthly.loc[rev.idxmin()]
lines = [
 f"- Total delivered revenue: {tot:,.0f} BDT from {orders_total:,} delivered orders (average order value {tot/orders_total:,.0f} BDT).",
 f"- Best month: {best['month']} ({best['revenue']:,.0f} BDT). Weakest month: {lo['month']} ({lo['revenue']:,.0f} BDT).",
 f"- {top_cat['category']} gives {share:.1f}% of revenue ({top_cat['revenue']:,.0f} BDT).",
 f"- Highest revenue city: {city.iloc[0]['city']} ({city.iloc[0]['revenue']:,.0f} BDT); highest average order value: {city.sort_values('avg_order_value').iloc[-1]['city']} ({city['avg_order_value'].max():,.0f} BDT).",
 f"- Highest cancel rate by payment method: {pay.iloc[0]['payment_method']} ({pay.iloc[0]['cancel_rate_pct']}%); highest return rate: {pay.sort_values('return_rate_pct').iloc[-1]['payment_method']} ({pay['return_rate_pct'].max()}%).",
 f"- Data quality: {int(dq['records_affected'].sum())} problem records found in the raw files; the cleaning step removed or fixed them (see reports/cleaning_log.csv).",
]
open("reports/key_findings.md", "w").write("# Key findings (generated from the SQL results)\n\n" + "\n".join(lines) + "\n")
print("\n".join(lines))
