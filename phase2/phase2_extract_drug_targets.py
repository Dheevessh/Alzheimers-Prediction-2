import pandas as pd

bbb = pd.read_csv("../database/bbb_positive_drugs.csv")
dt  = pd.read_csv("../database/drug_target_interactions.csv")

print("BBB file shape:", bbb.shape)
print("Drug-target file shape:", dt.shape)

print("BBB columns:", bbb.columns.tolist())
print("Drug-target columns:", dt.columns.tolist())

alz_targets = set([
    # Amyloid
    "APP","BACE1","PSEN1","PSEN2","ADAM10",

    # Tau / kinases
    "MAPT","GSK3B","CDK5","MARK4",

    # Neuroinflammation
    "TNF","IL1B","IL6","TREM2","CSF1R",

    # Lipid / genetic risk
    "APOE","CLU","BIN1",

    # Synapse / neurotransmission
    "ACHE","GRIN2B",

    # Oxidative stress / mitochondria
    "SOD1","SOD2","NFE2L2"
])

name_col = None
for c in ["compound_name", "drug_name", "name"]:
    if c in bbb.columns:
        name_col = c
        break

if name_col is None:
    raise ValueError("No drug-name column found in bbb_positive_drugs.csv")

print("Using drug name column:", name_col)

dt = dt.copy()

# Standardize column names if needed
if "target_gene" not in dt.columns and "target_name" in dt.columns:
    dt = dt.rename(columns={"target_name": "target_gene"})
if "target_gene" not in dt.columns and "gene_symbol" in dt.columns:
    dt = dt.rename(columns={"gene_symbol": "target_gene"})
if "drug_name" not in dt.columns and "compound_name" in dt.columns:
    dt = dt.rename(columns={"compound_name": "drug_name"})

dt["drug_name"] = dt["drug_name"].astype(str)
dt["target_gene"] = dt["target_gene"].astype(str)

drug_to_targets = (
    dt.groupby("drug_name")["target_gene"]
    .apply(lambda s: set(t for t in s if t and t != "nan"))
    .to_dict()
)

rows = []

for drug in bbb[name_col].dropna().astype(str).unique():
    targets = drug_to_targets.get(drug, set())
    ad_hits = targets.intersection(alz_targets)

    rows.append({
        "drug_name": drug,
        "num_targets": len(targets),
        "num_ad_targets": len(ad_hits),
        "ad_hit_targets": ";".join(sorted(ad_hits)) if ad_hits else "",
        "ad_target_ratio": len(ad_hits) / max(len(targets), 1)
    })

feat = pd.DataFrame(rows)
feat.head()

out = feat.merge(
    bbb,
    left_on="drug_name",
    right_on=name_col,
    how="left"
)

if "bbb_score" in out.columns:
    out["phase2_score"] = (
        0.5 * out["ad_target_ratio"] +
        0.5 * out["bbb_score"].fillna(0)
    )
else:
    out["phase2_score"] = out["ad_target_ratio"]

out = out.sort_values("phase2_score", ascending=False)

out.to_csv("outputs/phase2_scored_drugs.csv", index=False)
print("✅ Saved phase2_scored_drugs.csv")
out.head(20)

