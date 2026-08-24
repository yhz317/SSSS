import pandas as pd
import requests
import time
import os
import re
from tqdm import tqdm

# ================== CONFIG ==================
API_KEY = os.environ.get("ELSEVIER_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "ELSEVIER_API_KEY is not set. Set it before downloading PDFs."
    )
CSV_PATH = (
    r"D:\Github\SSSS\results\topics\251209_DHC_23-25"
    r"\summary_filtered.csv"
)
DELAY = 1.2
DOI_COLUMN = "doi"
# ============================================

# 🔹 Derive base directory from CSV location
BASE_DIR = os.path.dirname(CSV_PATH)
OUT_DIR = os.path.join(BASE_DIR, "elsevier_pdfs")
LOG_OK = os.path.join(BASE_DIR, "downloaded.log")
LOG_FAIL = os.path.join(BASE_DIR, "non_elsevier.log")

os.makedirs(OUT_DIR, exist_ok=True)

headers = {
    "X-ELS-APIKey": API_KEY,
    "Accept": "application/pdf"
}


def safe_filename(doi: str) -> str:
    return re.sub(r"[^\w\-_.]", "_", doi) + ".pdf"


df = pd.read_csv(CSV_PATH)

if DOI_COLUMN not in df.columns:
    raise ValueError(f"DOI column '{DOI_COLUMN}' not found in CSV")

dois = (
    df[DOI_COLUMN]
    .dropna()
    .astype(str)
    .str.strip()
    .str.lower()
    .str.replace(r"^https?://(dx\.)?doi\.org/", "", regex=True)
    .unique()
)

print(f"Found {len(dois)} unique DOIs")

downloaded = 0
skipped = 0

try:
    for doi in tqdm(dois, desc="Downloading PDFs"):
        filename = safe_filename(doi)
        filepath = os.path.join(OUT_DIR, filename)

        # Resume-safe
        if os.path.exists(filepath):
            continue

        url = f"https://api.elsevier.com/content/article/doi/{doi}"
        r = requests.get(url, headers=headers)

        if r.status_code == 200 and "pdf" in r.headers.get("Content-Type", ""):
            with open(filepath, "wb") as f:
                f.write(r.content)

            with open(LOG_OK, "a", encoding="utf-8") as log:
                log.write(doi + "\n")

            downloaded += 1
        else:
            with open(LOG_FAIL, "a", encoding="utf-8") as log:
                log.write(f"{doi}\t{r.status_code}\n")

            skipped += 1

        time.sleep(DELAY)

except KeyboardInterrupt:
    print("\n⛔ Interrupted by user. Progress saved safely.")

print("\n========== SUMMARY ==========")
print(f"Downloaded PDFs : {downloaded}")
print(f"Skipped          : {skipped}")
print(f"Output folder    : {OUT_DIR}")
