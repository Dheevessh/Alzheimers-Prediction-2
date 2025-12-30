# Inputs:
#   bbb_positive_drugs.csv
#   chembl_drug_mechanism_curated.csv
#   ad_genes_disgenet.csv
#
# Outputs:
#   phase2_scored_drugs.csv
#   phase2_report.txt

import pandas as pd
import re

def norm_name(x: str) -> str:
    if pd.isna(x):
        return ""
    x = str(x).lower()
    x = re.sub(r"\(.*?\)", "", x)
    x = re.sub(r"[^a-z0-9\s]", " ", x)
    x = re.sub(r"\s+", " ", x).strip()
    return x

print("🚀 Phase 2 v3 scoring started (pathology-focused)")

# --------------------------
# 1) Load inputs
# --------------------------
bbb = pd.read_csv("../database/bbb_positive_drugs.csv")
moa = pd.read_csv("../database/chembl_drug_mechanism_curated.csv")
ad  = pd.read_csv("../database/ad_genes_disgenet.csv")

# --------------------------
# 2) Detect BBB drug column
# --------------------------
bbb_name_col = None
for c in ["compound_name", "drug_name", "name"]:
    if c in bbb.columns:
        bbb_name_col = c
        break
if bbb_name_col is None:
    raise SystemExit(f"❌ BBB file missing drug name column. Columns: {bbb.columns.tolist()}")

bbb["drug_norm"] = bbb[bbb_name_col].apply(norm_name)

if "drug_name" not in moa.columns:
    raise SystemExit(f"❌ chembl_drug_mechanism_curated.csv missing drug_name. Columns: {moa.columns.tolist()}")

moa["drug_norm"] = moa["drug_name"].apply(norm_name)

# Choose best target identifier: gene symbol if present, else target name
moa["target_gene"] = moa.get("target_gene", "").fillna("").astype(str).str.strip()
moa["target_name"] = moa.get("target_name", "").fillna("").astype(str).str.strip()

moa["target_best"] = moa["target_gene"]
mask_empty = moa["target_best"].eq("")
moa.loc[mask_empty, "target_best"] = moa.loc[mask_empty, "target_name"]

moa["t_upper"] = moa["target_best"].astype(str).str.upper()

# AD gene set (broad)
ad_genes_upper = set(ad["gene_symbol"].astype(str).str.strip().str.upper().tolist())

# --------------------------
# 3) Define pathology-focused modules
# --------------------------
# Core disease-modifying modules
AMYLOID  = {"APP","BACE1","PSEN1","PSEN2","ADAM10"}
TAU      = {"MAPT","GSK3B","CDK5","MARK4","CSNK1D","CSNK1E"}  # add casein kinases (tau-related)
MICROGLIA= {"TREM2","CSF1R","TYROBP","SPI1"}                  # microglia/immune genetics
LIPID    = {"APOE","CLU","ABCA7","SORL1"}

CORE = AMYLOID | TAU | MICROGLIA | LIPID

# Secondary supportive modules (still relevant, lower weight)
INFLAM = {"TNF","IL1B","IL6","NFKB1","PTGS2"}
MITO_OX= {"NFE2L2","SOD1","SOD2","PPARGC1A","PINK1","PARK7"}

SECONDARY = INFLAM | MITO_OX

# Symptomatic / nonspecific CNS targets that we DO NOT want to dominate Phase 2
# (These are not "wrong", but they aren't disease-modifying signals.)
EXCLUDE_PREFIXES = (
    "DRD",   # dopamine receptors
    "HTR",   # serotonin receptors
    "ADRA",  # adrenergic receptors
    "CHRM",  # muscarinic receptors
    "GABR",  # GABA receptors
    "OPR",   # opioid receptors
)

# Explicitly downweight or exclude a few frequent offenders
EXCLUDE_EXACT = {
    "NR3C1",  # glucocorticoid receptor: broad stress response
    "CNR1",   # cannabinoid receptor 1
}

# Symptomatic Alzheimer target (keep, but low weight)
LOW_SYMP = {"ACHE"}

def is_excluded_target(t: str) -> bool:
    t = str(t).upper().strip()
    if t in EXCLUDE_EXACT:
        return True
    return any(t.startswith(p) for p in EXCLUDE_PREFIXES)

def target_weight(t: str) -> float:
    t = str(t).upper().strip()

    if is_excluded_target(t):
        return 0.0

    if t in CORE:
        return 5.0

    if t in SECONDARY:
        return 2.0

    if t in LOW_SYMP:
        return 0.25

    # Broad AD genes from DisGeNET: very low weight (prevents NR3C1/DRD-like dominance)
    if t in ad_genes_upper:
        return 0.5

    return 0.0

moa["w"] = moa["t_upper"].apply(target_weight)
moa["is_core_hit"] = moa["t_upper"].isin(CORE)

# --------------------------
# 4) Drug-level features
# --------------------------
# Total distinct targets in curated MOA set
num_targets_moa = moa.groupby("drug_norm")["t_upper"].nunique()

# Weighted AD score across targets
moa_w = moa[moa["w"] > 0].copy()
ad_weight_sum = moa_w.groupby("drug_norm")["w"].sum()

# Core hits count (STRICT)
core_hits = moa.groupby("drug_norm")["is_core_hit"].sum()

# List of hit targets (only those with w>0)
ad_hit_targets = moa_w.groupby("drug_norm")["t_upper"].apply(lambda s: ";".join(sorted(set(s))))

features = pd.DataFrame({
    "drug_norm": num_targets_moa.index,
    "num_targets_moa": num_targets_moa.values
}).merge(
    ad_weight_sum.rename("ad_weight_sum"),
    on="drug_norm",
    how="left"
).merge(
    core_hits.rename("num_core_hits"),
    on="drug_norm",
    how="left"
).merge(
    ad_hit_targets.rename("ad_hit_targets"),
    on="drug_norm",
    how="left"
)

features["ad_weight_sum"]  = features["ad_weight_sum"].fillna(0.0)
features["num_core_hits"]  = features["num_core_hits"].fillna(0).astype(int)
features["ad_hit_targets"] = features["ad_hit_targets"].fillna("")

# --------------------------
# 5) Merge with BBB list
# --------------------------
out = bbb.merge(features, on="drug_norm", how="left")
out["num_targets_moa"] = out["num_targets_moa"].fillna(0).astype(int)
out["ad_weight_sum"]   = out["ad_weight_sum"].fillna(0.0)
out["num_core_hits"]   = out["num_core_hits"].fillna(0).astype(int)
out["ad_hit_targets"]  = out["ad_hit_targets"].fillna("")
out["drug_name_out"]   = out[bbb_name_col].astype(str)

# --------------------------
# 6) Final scoring rules (pathology-focused)
# --------------------------
# Normalize by number of targets to avoid promiscuous domination
out["ad_score_norm"] = out["ad_weight_sum"] / out["num_targets_moa"].clip(lower=1)

# Hard requirement: must hit at least 1 core pathology gene to score fully
# Otherwise, heavily penalize (still keep a tiny score for secondary-only)
out["core_gate"] = (out["num_core_hits"] > 0).astype(int)

# You can tune these:
CORE_MULTIPLIER = 1.0
NONCORE_PENALTY = 0.05   # secondary-only gets 5% of score

out["ad_score_gated"] = out["ad_score_norm"] * (
    out["core_gate"] * CORE_MULTIPLIER + (1 - out["core_gate"]) * NONCORE_PENALTY
)

# Optionally include BBB score if you have it
if "bbb_score" in out.columns:
    out["phase2_score"] = 0.7 * out["ad_score_gated"] + 0.3 * out["bbb_score"].fillna(0)
else:
    out["phase2_score"] = out["ad_score_gated"]

out = out.sort_values("phase2_score", ascending=False)

# --------------------------
# 7) Save outputs
# --------------------------
out.to_csv("outputs/phase2_scored_drugs.csv", index=False)

top = out.head(30)[["drug_name_out", "num_targets_moa", "num_core_hits", "ad_hit_targets", "phase2_score"]]

with open("outputs/phase2_report.txt", "w", encoding="utf-8") as f:
    f.write(f"Total BBB+ drugs: {len(out)}\n")
    nonzero = (out["phase2_score"] > 0).sum()
    f.write(f"Non-zero Phase2 v3 score: {nonzero} ({100*nonzero/len(out):.2f}%)\n")
    f.write(f"Core-hit drugs (num_core_hits>0): {(out['num_core_hits']>0).sum()} ({100*(out['num_core_hits']>0).mean():.2f}%)\n\n")
    f.write("Top 30 candidates:\n")
    f.write(top.to_string(index=False))
    f.write("\n")

print("✅ Saved phase2_scored_drugs.csv")
print("✅ Saved phase2_report.txt")
print("\nTop 30 candidates:")
print(top)
