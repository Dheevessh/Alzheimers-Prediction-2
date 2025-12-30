# phase3/phase3_score.py
import pandas as pd

try:
    from .config import MODEL_WEIGHTS
except ImportError:
    from config import MODEL_WEIGHTS

# ----------------------------------
# Research-tool / anesthetic penalties
# ----------------------------------
TOOL_PENALTY_TERMS = [
    "anesthetic", "anaesthetic", "barbiturate", "sedative",
    "research tool", "experimental tool",
    "nmda antagonist", "dizocilpine", "mk-801",
    "thiopental", "ketamine", "propofol"
]

def apply_tool_penalty(drug_name: str, score: float) -> float:
    """
    Penalize compounds that are likely research tools or anesthetics
    rather than disease-modifying therapies.
    """
    if score <= 0:
        return score
    d = (drug_name or "").lower()
    if any(term in d for term in TOOL_PENALTY_TERMS):
        return score * 0.2
    return score


def paper_score(row):
    """
    Per-paper score:
    - rewards positive net signal (pos_hits - neg_hits)
    - caps signal so long abstracts don't dominate
    - adds outcome diversity bonus
    """
    base = MODEL_WEIGHTS.get(row.get("model", "unknown"), 0.2)

    pos = float(row.get("pos_hits", 0) or 0)
    neg = float(row.get("neg_hits", 0) or 0)

    signal = pos - neg
    if signal <= 0:
        return 0.0

    capped = min(signal, 6.0)

    outcomes = str(row.get("outcomes", "") or "")
    outcome_count = len([x for x in outcomes.split(";") if x.strip()])
    outcome_bonus = 0.3 * outcome_count

    return base * capped + outcome_bonus


def aggregate_drug_scores(df_papers: pd.DataFrame):
    """
    Drug-level aggregation:
    - sums paper_score
    - computes net positivity (n_positive - n_negative)
    - computes signed_score (direction-aware)
    - applies research-tool penalties
    - returns sorted dataframe
    """

    if df_papers is None or df_papers.empty:
        return pd.DataFrame(columns=[
            "drug", "signed_score", "evidence_score", "n_papers",
            "n_positive", "n_negative", "net_positive",
            "models", "confidence"
        ])

    df = df_papers.copy()
    df["paper_score"] = df.apply(paper_score, axis=1)

    agg = df.groupby("drug").agg(
        evidence_score=("paper_score", "sum"),
        n_papers=("paper_score", "count"),
        n_positive=("direction", lambda s: (s == "positive").sum()),
        n_negative=("direction", lambda s: (s == "negative").sum()),
        models=("model", lambda s: ";".join(sorted(set(s))))
    ).reset_index()

    # Prevent "volume-only" domination
    agg["evidence_score"] = agg["evidence_score"].clip(upper=50)

    # Net positivity
    agg["net_positive"] = agg["n_positive"] - agg["n_negative"]

    # ----------------------------
    # Signed score (core ranking)
    # ----------------------------
    agg["signed_score"] = agg["evidence_score"] * (1 + 0.15 * agg["net_positive"])

    # Heavy penalty if evidence is neutral or negative
    agg.loc[agg["net_positive"] <= 0, "signed_score"] = (
        agg.loc[agg["net_positive"] <= 0, "evidence_score"] * 0.05
    )

    # ----------------------------
    # Apply research-tool penalty
    # ----------------------------
    agg["signed_score"] = agg.apply(
        lambda r: apply_tool_penalty(r["drug"], r["signed_score"]),
        axis=1
    )

    # ----------------------------
    # Confidence proxy
    # ----------------------------
    agg["confidence"] = (
        (agg["n_papers"].clip(upper=20) / 20.0) +
        (agg["models"].str.count(";").clip(upper=4) / 4.0)
    ) / 2.0

    # Final sort
    agg = agg.sort_values("signed_score", ascending=False)

    return agg
