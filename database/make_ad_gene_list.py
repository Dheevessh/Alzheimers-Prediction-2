import pandas as pd
import requests

# Harmonizome gene set page (contains a real HTML table with columns: Symbol, Name)
URL = "https://maayanlab.cloud/Harmonizome/gene_set/Alzheimer%2BDisease/DisGeNET%2BGene-Disease%2BAssociations"

print("Downloading AD gene set page...")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
r = requests.get(URL, headers=headers, timeout=60)
r.raise_for_status()

html = r.text
print("Downloaded characters:", len(html))

# ---- Method 1: Parse HTML tables (most reliable) ----
tables = pd.read_html(html)
print("Tables found:", len(tables))

# Find the table that contains the "Symbol" column
gene_table = None
for t in tables:
    cols = [str(c).strip().lower() for c in t.columns]
    if "symbol" in cols:
        gene_table = t
        break

if gene_table is None:
    # Save the HTML so you can inspect what you actually downloaded
    with open("harmonizome_ad_page_debug.html", "w", encoding="utf-8") as f:
        f.write(html)
    raise SystemExit(
        "❌ Could not find a table with a 'Symbol' column.\n"
        "I saved the downloaded page as harmonizome_ad_page_debug.html — open it and search for 'Symbol'."
    )

# Standardize column name and extract symbols
# Sometimes the column could be "Symbol" with different case
symbol_col = None
for c in gene_table.columns:
    if str(c).strip().lower() == "symbol":
        symbol_col = c
        break

genes = (
    gene_table[symbol_col]
    .astype(str)
    .str.strip()
    .dropna()
    .unique()
)

genes = sorted(set(genes))

df = pd.DataFrame({"gene_symbol": genes})
df.to_csv("ad_genes_disgenet.csv", index=False)

print("✅ Saved ad_genes_disgenet.csv")
print("Gene count:", len(df))
print(df.head(20))
