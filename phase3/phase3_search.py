# phase3/phase3_search.py
import os
import json
import time
import hashlib
import requests
from tqdm import tqdm

try:
    from .config import CACHE_DIR, MAX_PAPERS_PER_DRUG
except ImportError:
    from config import CACHE_DIR, MAX_PAPERS_PER_DRUG

EPMC_API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

def safe_cache_name(drug: str) -> str:
    """
    Generate a filesystem-safe cache filename using hash.
    """
    h = hashlib.sha1(drug.encode("utf-8")).hexdigest()[:16]
    return f"epmc_{h}.json"

def fetch_drug_papers(drug: str):
    cache_name = safe_cache_name(drug)
    cache_path = os.path.join(CACHE_DIR, cache_name)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    params = {
        "query": f'"{drug}" AND Alzheimer',
        "format": "json",
        "pageSize": MAX_PAPERS_PER_DRUG,
        "resultType": "core"
    }

    try:
        r = requests.get(EPMC_API, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        papers = data.get("resultList", {}).get("result", [])
    except Exception as e:
        print(f"⚠️ API error for {drug}: {e}")
        papers = []

    # De-duplicate by PMID/DOI
    seen = set()
    dedup = []
    for p in papers:
        key = p.get("pmid") or p.get("doi")
        if key and key not in seen:
            seen.add(key)
            dedup.append(p)

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(dedup, f, indent=2)

    time.sleep(1.0)  # be polite to API
    return dedup

def batch_fetch(drugs):
    all_papers = {}
    for drug in tqdm(drugs, desc="Searching Europe PMC"):
        all_papers[drug] = fetch_drug_papers(drug)
    return all_papers
