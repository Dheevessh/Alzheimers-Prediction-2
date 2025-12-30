# phase2_extract_chembl_mechanism_curated.py
# Uses your local ChEMBL SQLite:
# - Download page: https://chembl.gitbook.io/chembl-interface-documentation/downloads  (ChEMBL 36)  :contentReference[oaicite:7]{index=7}

import sqlite3
import pandas as pd

DB_PATH = "chembl_36.db"

def table_cols(conn, table):
    return pd.read_sql(f"PRAGMA table_info({table});", conn)["name"].tolist()

conn = sqlite3.connect(DB_PATH)

# --- verify required tables exist ---
tables = set(pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)["name"].tolist())
required = {"drug_mechanism", "molecule_dictionary", "target_dictionary"}
missing = [t for t in required if t not in tables]
if missing:
    raise SystemExit(f"❌ Missing required tables in DB: {missing}")

dm_cols = table_cols(conn, "drug_mechanism")
md_cols = table_cols(conn, "molecule_dictionary")
td_cols = table_cols(conn, "target_dictionary")

# drug_mechanism keys vary by release/schema: usually molregno + tid
dm_mol = "molregno" if "molregno" in dm_cols else None
dm_tid = "tid" if "tid" in dm_cols else None
dm_action = "action_type" if "action_type" in dm_cols else None

if not dm_mol or not dm_tid:
    raise SystemExit(f"❌ Can't find molregno/tid in drug_mechanism columns: {dm_cols}")

# molecule_dictionary fields for filtering
md_mol = "molregno" if "molregno" in md_cols else None
md_name = "pref_name" if "pref_name" in md_cols else None
md_type = "molecule_type" if "molecule_type" in md_cols else None
md_phase = "max_phase" if "max_phase" in md_cols else None
md_ther = "therapeutic_flag" if "therapeutic_flag" in md_cols else None

if not md_mol or not md_name or not md_phase:
    raise SystemExit(f"❌ Can't find needed columns in molecule_dictionary: {md_cols}")

# target_dictionary fields
td_tid = "tid" if "tid" in td_cols else None
td_name = "pref_name" if "pref_name" in td_cols else None
td_chembl = "target_chembl_id" if "target_chembl_id" in td_cols else None

if not td_tid:
    raise SystemExit(f"❌ Can't find tid in target_dictionary columns: {td_cols}")

# Optional gene symbol mapping via target_components + component_synonyms
has_tc = "target_components" in tables
has_cs = "component_synonyms" in tables

gene_join = ""
gene_select = "NULL AS target_gene"

if has_tc and has_cs:
    tc_cols = table_cols(conn, "target_components")
    cs_cols = table_cols(conn, "component_synonyms")

    if "tid" in tc_cols and "component_id" in tc_cols and "component_id" in cs_cols and "syn_type" in cs_cols and "component_synonym" in cs_cols:
        gene_join = """
        LEFT JOIN target_components tc ON t.tid = tc.tid
        LEFT JOIN component_synonyms cs
            ON tc.component_id = cs.component_id AND cs.syn_type = 'GENE_SYMBOL'
        """
        gene_select = "MAX(cs.component_synonym) AS target_gene"

# --- Filtering rules (scientific cleanup) ---
# Keep: clinical+ small molecules, with a real pref_name
filters = []
filters.append("m.pref_name IS NOT NULL")
filters.append("m.max_phase >= 1")  # clinical phase or approved

if md_type:
    filters.append("m.molecule_type = 'Small molecule'")

if md_ther:
    # keep therapeutic_flag = 1 when present
    filters.append("(m.therapeutic_flag = 1)")

where_clause = " AND ".join(filters)

sql = f"""
SELECT
    m.pref_name AS drug_name,
    m.max_phase AS max_phase,
    {('m.molecule_type AS molecule_type,' if md_type else "'unknown' AS molecule_type,")}
    {('m.therapeutic_flag AS therapeutic_flag,' if md_ther else "NULL AS therapeutic_flag,")}
    {('t.target_chembl_id AS target_chembl_id,' if td_chembl else "NULL AS target_chembl_id,")}
    {('t.pref_name AS target_name,' if td_name else "NULL AS target_name,")}
    {gene_select},
    dm.{dm_action} AS mechanism
FROM drug_mechanism dm
JOIN molecule_dictionary m ON dm.{dm_mol} = m.{md_mol}
JOIN target_dictionary t ON dm.{dm_tid} = t.{td_tid}
{gene_join}
WHERE {where_clause}
GROUP BY
    m.pref_name, m.max_phase
    {(', m.molecule_type' if md_type else '')}
    {(', m.therapeutic_flag' if md_ther else '')}
    {(', t.target_chembl_id' if td_chembl else '')}
    {(', t.pref_name' if td_name else '')}
    , dm.{dm_action}
"""

print("Running curated mechanism extraction...")
df = pd.read_sql(sql, conn)
conn.close()

# Clean target_gene fallback
df["target_gene"] = df["target_gene"].fillna("").astype(str)
df["target_name"] = df["target_name"].fillna("").astype(str)

df.to_csv("chembl_drug_mechanism_curated.csv", index=False)
print("✅ Saved chembl_drug_mechanism_curated.csv")
print("Rows:", len(df))
print(df.head(20))
