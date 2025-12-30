# phase3/phase3_extract.py

try:
    from .config import POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS, OUTCOME_KEYWORDS
except ImportError:
    from config import POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS, OUTCOME_KEYWORDS

# Strict Alzheimer pathology terms
AD_TERMS = [
    "alzheimer", "alzheimer's disease",
    "amyloid plaque", "aβ plaque",
    "phospho-tau", "tau tangle", "tauopathy"
]

# Strong preclinical AD model markers
AD_MODEL_MARKERS = [
    "app/ps1", "5xfad", "3xtg", "tg2576", "p301s",
    "transgenic mouse", "morris water maze",
    "y-maze", "novel object recognition"
]

def contains_any(text: str, terms) -> bool:
    t = (text or "").lower()
    return any(term in t for term in terms)

def has_any_outcome(text: str) -> bool:
    t = (text or "").lower()
    for kws in OUTCOME_KEYWORDS.values():
        if any(k.lower() in t for k in kws):
            return True
    return False

def detect_model(text: str) -> str:
    t = (text or "").lower()

    if any(k in t for k in ["phase ii", "phase iii", "double-blind", "placebo"]):
        return "clinical"
    if any(k in t for k in ["cohort", "case-control", "observational"]):
        return "human_observational"
    if any(k in t for k in ["mouse", "mice", "rat", "transgenic", "5xfad", "3xtg", "app/ps1"]):
        return "animal"
    if any(k in t for k in ["cell", "in vitro", "neuronal culture", "primary neurons"]):
        return "cell"

    return "unknown"

def keyword_hits(text: str, keywords) -> int:
    t = (text or "").lower()
    return sum(1 for k in keywords if k.lower() in t)

def outcome_tags(text: str):
    tags = []
    t = (text or "").lower()
    for outcome, kws in OUTCOME_KEYWORDS.items():
        if any(k.lower() in t for k in kws):
            tags.append(outcome)
    return tags

def extract_evidence(drug: str, paper: dict):
    """
    Extracts AD-relevant evidence from a single paper.
    Returns None if paper fails strict AD + model + outcome gates.
    """

    title = paper.get("title", "") or ""
    abstract = paper.get("abstractText", "") or ""
    text = f"{title}\n{abstract}"

    # -------------------------------
    # HARD SCIENTIFIC GATES
    # -------------------------------
    if not contains_any(text, AD_TERMS):
        return None

    if not contains_any(text, AD_MODEL_MARKERS):
        return None

    if not has_any_outcome(text):
        return None

    # -------------------------------
    # Scoring features
    # -------------------------------
    pos = keyword_hits(text, POSITIVE_KEYWORDS)
    neg = keyword_hits(text, NEGATIVE_KEYWORDS)

    model = detect_model(text)
    outcomes = outcome_tags(text)

    direction = "neutral"
    if pos > neg and pos > 0:
        direction = "positive"
    elif neg > pos and neg > 0:
        direction = "negative"

    return {
        "drug": drug,
        "title": title,
        "pmid": paper.get("pmid"),
        "doi": paper.get("doi"),
        "journal": paper.get("journalTitle"),
        "pub_year": paper.get("pubYear"),
        "model": model,
        "direction": direction,
        "pos_hits": pos,
        "neg_hits": neg,
        "outcomes": ";".join(outcomes),
        "abstract": abstract[:8000],
    }
