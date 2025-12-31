# 🧠 AI-Driven Alzheimer’s Drug Discovery

This project is an end-to-end **drug candidate prioritization pipeline** for Alzheimer’s disease.  
It combines:
- **Phase 1:** Blood–Brain Barrier (BBB) screening (Machine Learning Classifier)
- **Phase 2:** Mechanistic plausibility scoring using drug–target interactions (ChEMBL/DisGeNET)
- **Phase 3:** Live biomedical literature mining using Europe PMC (public API)
- **Final:** A merged score that ranks candidates for demo and review

> ⚠️ **Important:** This system **does not claim clinical efficacy**.  
> It produces a **ranked shortlist of candidates** based on mechanistic plausibility + literature evidence.

---

## 💡 About The Project

Developing a single Alzheimer’s drug takes **10+ years** and costs **billions**, yet **99% fail** in human trials. We realized the traditional "trial and error" method on animals is broken.

Inspired by the **FDA Modernization Act 2.0**—which now allows computer models to replace animal testing—we built a **24/7 Virtual Scientist**. Our goal is to use AI to instantly identify safe, existing drugs that can be repurposed for Alzheimer's, skipping years of slow and expensive pre-clinical work.

---

## 📦 1. Installation & Setup

First, ensure you have **Python 3.10+** installed. Then, install the required dependencies:

```markdown
pip install -r requirements.txt
```

---

## 🛠 2. Data Preparation & Exploration

**Crucial Step:** Before running the pipeline, you must generate the reference databases (Alzheimer's gene lists and ChEMBL mechanism data).

```markdown
python database/inspect_db.py
python database/make_ad_gene_list.py
python database/extract_chembl_mechanism_curated.py
```

**Outputs:**
- `database/ad_genes_disgenet.csv` (Curated list of Alzheimer's targets)
- `database/chembl_mechanism_curated.csv` (Cleaned mechanism data)

---

## 🚀 3. Running the Pipeline

The pipeline is divided into three distinct phases. Run them in the following order:

### Stage 1: Blood–Brain Barrier Screening
Predicts which drugs can cross the blood-brain barrier (BBB) using a Random Forest classifier trained on the B3DB dataset.

```markdown
python phase1/predict_bbb_drugs.py
```
**Output:** `phase1/outputs/bbb_positive_drugs.csv`

### Stage 2: Mechanistic Plausibility Scoring
Scores drugs based on their biological targets (e.g., Amyloid, Tau) using the files generated in Step 2.

```markdown
python phase2/phase2_scoring.py
```

**(Optional Quality Checks):**
```markdown
python phase2/phase2_quality_check.py
python phase2/phase2_evaluation.py
```
**Output:** `phase2/outputs/phase2_scored_drugs.csv`

### Stage 3: Literature Mining
> ⚠️ **Warning:** This step uses the Europe PMC API and can take **30–180 minutes** depending on the number of drugs.
>
> **Tip:** Limit the number of drugs in `phase3_run_all.py` for testing purposes.

```markdown
python -m phase3.phase3_run_all
```

**Outputs:**
- `phase3/outputs/phase3_papers.csv` (Raw extracted evidence)
- `phase3/outputs/phase3_lit_evidence.csv` (Aggregated scores)
- `phase3/outputs/phase3_report.txt` (Summary text)

---

## 🏆 4. Final Results

Once all stages are complete, merge the biological and literature scores to generate the final ranked leaderboard.

```markdown
python final_merge.py
```

**Final Output:** `final_ranked_candidates.csv`

---

## 📊 5. Run the Dashboard (UI)

Explore the results and evidence interactively using the local web dashboard.

```markdown
streamlit run ui/app.py
```
Open your browser to the URL shown (usually `http://localhost:8501`).

---

## 📁 Project Structure

```plaintext
├── final_merge.py              # Main logic to combine Phase 2 & 3
├── requirements.txt            # Project dependencies
├── database/                   # Data Prep Scripts
│   ├── make_ad_gene_list.py    
│   └── extract_chembl_mechanism_curated.py
├── phase1/
│   └── predict_bbb_drugs.py    # BBB Classifier
├── phase2/
│   ├── phase2_scoring.py       # Mechanism Scoring Engine
│   └── phase2_quality_check.py # Novelty/Target validation
├── phase3/
│   └── phase3_run_all.py       # Literature Mining Controller
└── ui/
    └── app.py                  # Streamlit Dashboard
```

---

## 🛠 Built With

- **Languages:** Python 3.10
- **AI/ML:** Scikit-learn (RandomForest), BioBERT
- **Data:** Pandas, NumPy, ChEMBL, DisGeNET, Europe PMC API
- **App:** Streamlit