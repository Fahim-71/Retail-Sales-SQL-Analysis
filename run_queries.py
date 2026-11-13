"""Run every query in sql/queries.sql and save each result to reports/sql_results/."""
import re, sqlite3, os, pandas as pd
os.makedirs("reports/sql_results", exist_ok=True)
sql = open("sql/queries.sql").read()
con = sqlite3.connect("data/retail.db")
for m in re.finditer(r"-- (Q\d+): (.*?)\n(.*?);\s*(?=\n-- Q|\Z)", sql, re.S):
    qid, title, query = m.group(1), m.group(2), m.group(3)
    df = pd.read_sql_query(query, con)
    df.to_csv(f"reports/sql_results/{qid}.csv", index=False)
    print(f"\n{qid}: {title}\n{df.head(6).to_string(index=False)}")
