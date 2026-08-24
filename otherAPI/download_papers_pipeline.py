import pandas as pd
import requests
import time
import os
import re
from tqdm import tqdm

# ===================== CONFIG =====================
API_KEY = os.environ.get("ELSEVIER_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "ELSEVIER_API_KEY is not set. Set it before downloading papers."
    )
CSV_PATH = (
    r"D:\Github\SSSS\results\topics\251209_DHC_23-25"
    r"\summary_filtered.csv"
)  # ← 改这里
DOI_COLUMN = "doi"

ELSEVIER_DELAY = 1.2
UNPAYWALL_DELAY = 1.0
UNPAYWALL_EMAIL = "yh.z@tamu.edu"  # Unpaywall 要求填写
# =================================================

# ---------- Paths ----------
BASE_DIR = os.path.dirname(CSV_PATH)

ELSEVIER_DIR = os.path.join(BASE_DIR, "elsevier_pdfs")
OA_DIR = os.path.join(BASE_DIR, "oa_pdfs")
MISSING_DIR = os.path.join(BASE_DIR, "zotero_missing")

os.makedirs(ELSEVIER_DIR, exist_ok=True)
os.makedirs(OA_DIR, exist_ok=True)
os.makedirs(MISSING_DIR, exist_ok=True)

LOG_ELSEVIER = os.path.join(BASE_DIR, "downloaded_elsevier.log")
LOG_OA = os.path.join(BASE_DIR, "downloaded_oa.log")
LOG_MISSING = os.path.join(BASE_DIR, "zotero_missing.log")

MISSING_TXT = os.path.join(MISSING_DIR, "still_missing.txt")
MISSING_CSV = os.path.join(MISSING_DIR, "still_missing.csv")
STATS_FILE = os.path.join(BASE_DIR, "coverage_stats.txt")

# ---------- Helpers ----------


def normalize_doi(doi: str) -> str:
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi


def safe_filename(doi: str) -> str:
    return re.sub(r"[^\w\-_.]", "_", doi) + ".pdf"


# ---------- Load CSV ----------
df = pd.read_csv(CSV_PATH)

if DOI_COLUMN not in df.columns:
    raise ValueError(f"Column '{DOI_COLUMN}' not found in CSV")

df["doi_norm"] = (
    df[DOI_COLUMN]
    .dropna()
    .astype(str)
    .apply(normalize_doi)
)

dois = df["doi_norm"].unique()
total_dois = len(dois)

print(f"Found {total_dois} unique DOIs")

# ---------- Elsevier headers ----------
elsevier_headers = {
    "X-ELS-APIKey": API_KEY,
    "Accept": "application/pdf"
}

missing_rows = []

# ---------- Main Pipeline ----------
for doi in tqdm(dois, desc="Processing DOIs"):
    filename = safe_filename(doi)

    # ===== 1️⃣ Elsevier =====
    elsevier_path = os.path.join(ELSEVIER_DIR, filename)
    if not os.path.exists(elsevier_path):
        url = f"https://api.elsevier.com/content/article/doi/{doi}"
        r = requests.get(url, headers=elsevier_headers)

        if r.status_code == 200 and "pdf" in r.headers.get("Content-Type", ""):
            with open(elsevier_path, "wb") as f:
                f.write(r.content)

            with open(LOG_ELSEVIER, "a", encoding="utf-8") as log:
                log.write(doi + "\n")

            time.sleep(ELSEVIER_DELAY)
            continue

    # ===== 2️⃣ Unpaywall OA =====
    oa_path = os.path.join(OA_DIR, filename)
    if not os.path.exists(oa_path):
        up_url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
        up = requests.get(up_url)

        if up.status_code == 200:
            data = up.json()
            loc = data.get("best_oa_location")

            if loc and loc.get("url_for_pdf"):
                pdf_url = loc["url_for_pdf"]
                try:
                    pdf = requests.get(pdf_url, timeout=30)
                    if pdf.status_code == 200 and "pdf" in pdf.headers.get(
                            "Content-Type", ""):
                        with open(oa_path, "wb") as f:
                            f.write(pdf.content)

                        with open(LOG_OA, "a", encoding="utf-8") as log:
                            log.write(doi + "\n")

                        time.sleep(UNPAYWALL_DELAY)
                        continue
                except Exception:
                    pass

    # ===== 3️⃣ Still Missing =====
    with open(LOG_MISSING, "a", encoding="utf-8") as log:
        log.write(doi + "\n")

    with open(MISSING_TXT, "a", encoding="utf-8") as txt:
        txt.write(doi + "\n")

    missing_rows.append(df[df["doi_norm"] == doi].iloc[0])

# ---------- Save missing CSV ----------
if missing_rows:
    pd.DataFrame(missing_rows).drop(columns=["doi_norm"]).to_csv(
        MISSING_CSV, index=False
    )

# ---------- Coverage Statistics ----------
elsevier_count = len(os.listdir(ELSEVIER_DIR))
oa_count = len(os.listdir(OA_DIR))
missing_count = len(set(open(MISSING_TXT).read().splitlines())
                    ) if os.path.exists(MISSING_TXT) else 0

coverage = (elsevier_count + oa_count) / total_dois * 100

stats = f"""
========== COVERAGE STATISTICS ==========
Total DOIs        : {total_dois}
Elsevier PDFs     : {elsevier_count} ({elsevier_count/total_dois*100:.1f}%)
OA PDFs           : {oa_count} ({oa_count/total_dois*100:.1f}%)
Still missing     : {missing_count} ({missing_count/total_dois*100:.1f}%)
----------------------------------------
Overall coverage  : {coverage:.1f}%
========================================
"""

print(stats)

with open(STATS_FILE, "w", encoding="utf-8") as f:
    f.write(stats)
