# phase3/config.py

import os

# -------- Paths --------
# Resolve paths relative to this config file's location
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CONFIG_DIR)

# ---- Input list (Phase 2 output) ----
BBB_CSV_PATH = os.path.join(PROJECT_ROOT, "phase2", "outputs", "phase2_scored_drugs.csv")

# -------- Literature mining limits --------
MAX_PAPERS_PER_DRUG = 50   # safe default (increase later if needed)

# ---- Output/cache dirs ----
OUT_DIR = os.path.join(PROJECT_ROOT, "phase3", "outputs")
CACHE_DIR = os.path.join(PROJECT_ROOT, "phase3", "cache")

# ---- Europe PMC API ----
EUROPE_PMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

# ---- Alzheimer query building ----
# (used indirectly by search)
AD_QUERY_TERMS = [
    "Alzheimer", "amyloid", "Aβ", "Abeta", "tau", "microglia",
    "mitochondria", "synapse", "neuroinflammation", "cognition", "memory"
]

# ---- Evidence weights ----
MODEL_WEIGHTS = {
    "cell": 1.0,
    "animal": 2.0,
    "human_observational": 2.5,
    "clinical": 3.5,
    "unknown": 0.2
}

# ---- Extraction keywords (transparent + thesis-friendly) ----
POSITIVE_KEYWORDS = [
    "reduced", "decreased", "lowered", "improved", "rescued",
    "restored", "attenuated", "prevented", "protected",
    "inhibited", "suppressed"
]
NEGATIVE_KEYWORDS = [
    "increased", "worsened", "impaired", "elevated", "exacerbated",
    "toxicity", "neurotoxic", "aggravated"
]

OUTCOME_KEYWORDS = {
    "amyloid": ["amyloid", "aβ", "abeta", "plaque", "app", "bace1", "secretase"],
    "tau": ["tau", "phospho-tau", "hyperphosphorylation", "tangle", "mapt", "gsk3b", "cdk5"],
    "microglia": ["microglia", "neuroinflammation", "trem2", "csf1r", "tyrobp"],
    "mitochondria": ["mitochondria", "atp", "oxidative", "ros", "respiration", "membrane potential"],
    "synapse": ["synapse", "synaptic", "psd95", "spine", "synaptophysin"],
    "cognition": ["memory", "cognitive", "learning", "morris water maze", "y-maze", "novel object recognition"]
}
