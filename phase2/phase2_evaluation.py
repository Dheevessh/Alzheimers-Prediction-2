import pandas as pd

df = pd.read_csv("outputs/phase2_scored_drugs.csv")

print("Total:", len(df))
print("Columns:", df.columns.tolist())

print("\nScore stats:")
print(df["phase2_score"].describe())

nonzero = df[df["phase2_score"] > 0].copy()
print("\nNon-zero:", len(nonzero), f"({100*len(nonzero)/len(df):.2f}%)")

core = df[df["num_core_hits"] > 0].copy()
print("\nCore-hit drugs (num_core_hits>0):", len(core), f"({100*len(core)/len(df):.2f}%)")

print("\nTop 25:")
print(
    nonzero.sort_values("phase2_score", ascending=False).head(25)[
        ["drug_name_out", "num_targets_moa", "num_core_hits", "ad_hit_targets", "phase2_score"]
    ]
)

print("\nTop 25 CORE-HIT ONLY (this is your true shortlist):")
print(
    core.sort_values("phase2_score", ascending=False).head(25)[
        ["drug_name_out", "num_targets_moa", "num_core_hits", "ad_hit_targets", "phase2_score"]
    ]
)
