import pandas as pd
import re

df = pd.read_csv("outputs/phase2_scored_drugs.csv")

print("Total drugs:", len(df))
print("Non-zero:", (df["phase2_score"] > 0).sum())

# 1) How much ACHE dominates?
nonzero = df[df["phase2_score"] > 0].copy()
nonzero["has_ACHE"] = nonzero["ad_hit_targets"].fillna("").str.contains(r"\bACHE\b")
print("\nAmong non-zero drugs:")
print("Has ACHE:", nonzero["has_ACHE"].mean(), "(fraction)")

print("\nTop 30 (current scoring):")
print(df.sort_values("phase2_score", ascending=False).head(30)[
    ["compound_name", "num_targets_moa", "ad_hit_targets", "phase2_score"]
])

# 2) Flag likely non-drugs / junk names
def looks_junky(name: str) -> bool:
    if not isinstance(name, str):
        return True
    n = name.strip().lower()
    if n in {"-", ""}:
        return True
    if n.startswith(("chembl", "unii", "nsc")):
        return True
    if len(n) < 4:
        return True
    return False

df["junk_name"] = df["compound_name"].apply(looks_junky)

print("\nJunk-name drugs in top 100:",
      df.sort_values("phase2_score", ascending=False).head(100)["junk_name"].mean())

# 3) Filtered top list (more credible)
filtered = df[(~df["junk_name"]) & (df["num_targets_moa"] > 0) & (df["num_targets_moa"] <= 50)].copy()

print("\nFiltered top 30 (recommended shortlist):")
print(filtered.sort_values("phase2_score", ascending=False).head(30)[
    ["compound_name", "num_targets_moa", "ad_hit_targets", "phase2_score"]
])

print("\nDone.")
