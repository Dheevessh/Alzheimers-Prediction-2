# phase3/phase3_run_all.py
import os
import sys
import pandas as pd
from tqdm import tqdm

# Handle both direct script execution and package imports
try:
    from .config import BBB_CSV_PATH, OUT_DIR
    from .phase3_search import batch_fetch
    from .phase3_extract import extract_evidence
    from .phase3_score import aggregate_drug_scores
except ImportError:
    # Running as a direct script
    from config import BBB_CSV_PATH, OUT_DIR
    from phase3_search import batch_fetch
    from phase3_extract import extract_evidence
    from phase3_score import aggregate_drug_scores

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

def main():
    print("🔍 Phase 3 literature mining started")

    # -------------------------------
    # 1. Load Phase 2 / BBB drug list
    # -------------------------------
    bbb = pd.read_csv(BBB_CSV_PATH)

    # Robust drug-name column detection
    if "drug_name_out" in bbb.columns:
        name_col = "drug_name_out"
    elif "compound_name" in bbb.columns:
        name_col = "compound_name"
    elif "drug_name" in bbb.columns:
        name_col = "drug_name"
    else:
        name_col = bbb.columns[0]

    drugs = (
        bbb[name_col]
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .unique()
        .tolist()
    )

    drugs = sorted(drugs)

    # 🔧 DEBUG / SAFE MODE
    # Increase to 300–500 once stable
    drugs = drugs[:500]

    print(f"🧪 Running Phase 3 on {len(drugs)} drugs")

    # -------------------------------
    # 2. Literature search (API)
    # -------------------------------
    papers_by_drug = batch_fetch(drugs)

    # -------------------------------
    # 3. Evidence extraction
    # -------------------------------
    rows = []
    for drug, papers in tqdm(papers_by_drug.items(), desc="Extracting evidence"):
        for paper in papers:
            ev = extract_evidence(drug, paper)
            if ev is not None:
                rows.append(ev)

    if not rows:
        print("⚠️ No AD-relevant evidence extracted. Check gates.")
        return

    df_papers = pd.DataFrame(rows)
    df_papers.to_csv(
        os.path.join(OUT_DIR, "phase3_papers.csv"),
        index=False,
        encoding="utf-8"
    )

    print(f"📄 Saved {len(df_papers)} extracted papers")

    # -------------------------------
    # 4. Drug-level aggregation
    # -------------------------------
    df_drugs = aggregate_drug_scores(df_papers)

    df_drugs.to_csv(
        os.path.join(OUT_DIR, "phase3_lit_evidence.csv"),
        index=False,
        encoding="utf-8"
    )

    # -------------------------------
    # 5. Human-readable report
    # -------------------------------
    report_path = os.path.join(OUT_DIR, "phase3_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("Top 25 drugs by SIGNED Phase-3 evidence score\n")
        f.write("=" * 60 + "\n\n")
        f.write(df_drugs.head(25).to_string(index=False))
        f.write("\n\n")
        f.write("Columns explanation:\n")
        f.write("- signed_score: net-positive AD evidence (final rank)\n")
        f.write("- evidence_score: raw summed paper scores\n")
        f.write("- net_positive: positive − negative papers\n")
        f.write("- confidence: robustness proxy (papers + model diversity)\n")

    print("✅ Saved phase3_papers.csv")
    print("✅ Saved phase3_lit_evidence.csv")
    print("✅ Saved phase3_report.txt")

    print("\n🏆 Top 10 Phase-3 candidates:")
    print(
        df_drugs.head(10)[
            ["drug", "signed_score", "net_positive", "n_papers", "models"]
        ]
    )

    print("\n✅ Phase 3 complete")

if __name__ == "__main__":
    main()
