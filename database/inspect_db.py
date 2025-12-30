import sqlite3
import pandas as pd

DB_PATH = "chembl_36.db"
conn = sqlite3.connect(DB_PATH)

tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
print("Tables:", len(tables))
print(tables.to_string(index=False))

# Look for any table that sounds like drug mechanisms / drug-target
keywords = ["mechanism", "drug", "molecule", "target", "moa"]
print("\nPossible relevant tables:")
for t in tables["name"]:
    tl = t.lower()
    if any(k in tl for k in keywords):
        print(" -", t)

# Show columns for candidate tables
cands = [t for t in tables["name"] if any(k in t.lower() for k in keywords)]
print("\nColumns for candidate tables (first 10 columns shown):")
for t in cands[:20]:
    cols = pd.read_sql(f"PRAGMA table_info({t});", conn)
    print("\n==", t, "==")
    print(cols[["name","type"]].head(15).to_string(index=False))

conn.close()
