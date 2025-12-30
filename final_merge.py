# final_merge.py
import pandas as pd

PHASE2_PATH = "phase2/outputs/phase2_scored_drugs.csv" 
PHASE3_PATH = "phase3/outputs/phase3_lit_evidence.csv"
OUT_PATH    = "final_ranked_candidates.csv"

def minmax(s: pd.Series) -> pd.Series:
    s = s.fillna(0.0).astype(float)
    if s.max() == s.min():
        return s * 0.0
    return (s - s.min()) / (s.max() - s.min())

def main():
    p2 = pd.read_csv(PHASE2_PATH)
    p3 = pd.read_csv(PHASE3_PATH)

    # ---- detect name columns ----
    # Phase 2: prefer drug_name_out, else compound_name, else drug_name
    if "drug_name_out" in p2.columns:
        p2_name = "drug_name_out"
    elif "compound_name" in p2.columns:
        p2_name = "compound_name"
    elif "drug_name" in p2.columns:
        p2_name = "drug_name"
    else:
        p2_name = p2.columns[0]

    # Phase 3 column is "drug"
    p2["drug_key"] = p2[p2_name].astype(str).str.strip().str.lower()
    p3["drug_key"] = p3["drug"].astype(str).str.strip().str.lower()

    # ---- pick phase2 score column ----
    # use the best available
    if "phase2_score" in p2.columns:
        p2_score_col = "phase2_score"
    else:
        raise ValueError("No phase2 score column found in Phase 2 CSV.")

    # ---- merge ----
    merged = p2.merge(
        p3[["drug_key", "signed_score", "evidence_score", "net_positive", "n_papers", "models", "confidence"]],
        on="drug_key",
        how="left"
    )

    # Fill missing Phase 3 for drugs with no papers
    for c in ["signed_score", "evidence_score", "net_positive", "n_papers", "confidence"]:
        merged[c] = merged[c].fillna(0)

    merged["models"] = merged["models"].fillna("")

    # ---- normalize and final score ----
    # Hackathon-friendly weights:
    # - Phase 2: plausibility (target/mechanism) = 45%
    # - Phase 3: literature support (signed_score) = 45%
    # - Confidence = 10%
    merged["phase2_norm"] = minmax(merged[p2_score_col])
    merged["phase3_norm"] = minmax(merged["signed_score"])
    merged["conf_norm"]   = minmax(merged["confidence"])

    merged["final_score"] = (
        0.45 * merged["phase2_norm"] +
        0.45 * merged["phase3_norm"] +
        0.10 * merged["conf_norm"]
    )

    # Output nice columns
    out_cols = []

    # keep original display name column
    merged["drug_name"] = p2[p2_name].astype(str)
    out_cols.append("drug_name")

    # include SMILES if exists (great for demo UI)
    if "SMILES" in merged.columns:
        out_cols.append("SMILES")

    out_cols += [
        p2_score_col,
        "signed_score", "net_positive", "n_papers", "models", "confidence",
        "final_score"
    ]

    merged = merged.sort_values("final_score", ascending=False)

    merged[out_cols].to_csv(OUT_PATH, index=False)
    print("✅ Saved:", OUT_PATH)
    print("\nTop 15 candidates:")
    print(merged[out_cols].head(15).to_string(index=False))

if __name__ == "__main__":
    main()
