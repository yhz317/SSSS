import time
import SSSS.scholar as scholar
import pandas as pd
import numpy as np
import os
from random import random
import itertools
import requests
import re

# --- helper to look up DOI via Crossref ---
def lookup_doi(title, year=None):
    """
    Query Crossref for the given title (and optional year) 
    Returns the top-hit DOI or None.
    """
    params = {
        'query.bibliographic': title,
        'rows': 1
    }
    # if you want to filter by year:
    if year:
        # filter expects YYYY-MM-DD; we just use the year
        params['filter'] = f'from-pub-date:{year}-01-01,until-pub-date:{year}-12-31'
    # resp = requests.get('https://api.crossref.org/works', params=params)
    resp = requests.get(
    'https://api.crossref.org/works',
    params=params,
    timeout=(5, 5)   # 超时 8 秒，超时自动抛异常
    )
    resp.raise_for_status()
    items = resp.json().get('message', {}).get('items', [])
    if items:
        return items[0].get('DOI')
    return None

def lookup_metadata(title, year=None):
    """
    Query Crossref for the given title (and optional year) 
    Returns a dict with DOI, authors, issued date, abstract, link(s), and is-referenced-by-count.
    """
    params = {
        'query.bibliographic': title,
        'rows': 1,
        # only return the fields we care about
        'select': 'DOI,author,issued,abstract,link,is-referenced-by-count'
    }
    if year:
        params['filter'] = f'from-pub-date:{year}-01-01,until-pub-date:{year}-12-31'
    resp = requests.get(
        'https://api.crossref.org/works',
        params=params,
        timeout=(5, 5)
    )
    resp.raise_for_status()
    items = resp.json().get('message', {}).get('items', [])
    if not items:
        return {}
    item = items[0]

    # flatten authors into “Given Family; Given Family; …”
    authors = []
    for a in item.get('author', []):
        given = a.get('given', '').strip()
        family = a.get('family', '').strip()
        authors.append(' '.join(p for p in (given, family) if p))
    authors = '; '.join(authors)

    # get first date‑part array, e.g. [2020, 5, 12]
    date_parts = item.get('issued', {}).get('date-parts', [[None]])
    issued = '-'.join(str(p) for p in date_parts[0] if p is not None)

    # abstract may be HTML‑encoded
    abstract = item.get('abstract')
    # --- NEW: clean abstract HTML tags ---
    if abstract:
        abstract = re.sub('<.*?>', '', abstract)

    # link[] is an array of { URL, content-type, … }
    links = [l.get('URL') for l in item.get('link', [])]
    link = links[0] if links else None

    cited_by = item.get('is-referenced-by-count')

    return {
        'doi':              item.get('DOI'),
        'authors':          authors,
        'issued':           issued,
        'abstract':         abstract,
        'link':             link,
        'is_referenced_by_count': cited_by
    }

def safe_get(article, key, default=None):
    """
    Read raw attributes without triggering ScholarArticle network calls.
    """
    try:
        # Case 1: dict
        if isinstance(article, dict):
            return article.get(key, default)

        # Case 2: ScholarArticle
        # ScholarArticle stores parsed data in attrs
        if hasattr(article, "attrs"):
            return article.attrs.get(key, default)

        return default

    except Exception:
        return default

def normalize_field(raw):
    """
    Normalize a field from ScholarArticle safely.
    NEVER call str() on objects from scholar.py (they may trigger HTML parsing).
    """
    if raw is None:
        return None

    # Simple string
    if isinstance(raw, str):
        return raw.strip() if raw.strip() else None

    # Case: list → clean purely textual items only
    if isinstance(raw, list):
        texts = []
        for x in raw:
            # allow only plain strings
            if isinstance(x, str):
                txt = x.strip()
                if txt:
                    texts.append(txt)
        # Use longest string
        if texts:
            return max(texts, key=len)
        return None

    # int / float
    if isinstance(raw, (int, float)):
        return str(raw)

    # Other types (e.g., ScholarLink, HTMLNode) → ignore
    return None


def normalize_year(raw):
    if raw is None:
        return None

    # raw list
    if isinstance(raw, list):
        text_parts = [x for x in raw if isinstance(x, str)]
        big_str = " ".join(text_parts)
        nums = re.findall(r'\d{4}', big_str)
        for n in nums:
            year = int(n)
            if 1900 < year < 2100:
                return year
        return None

    # string → extract digit
    if isinstance(raw, str):
        nums = re.findall(r'\d{4}', raw)
        for n in nums:
            year = int(n)
            if 1900 < year < 2100:
                return year
        return None

    # numeric
    if isinstance(raw, (int, float)):
        y = int(raw)
        return y if 1900 < y < 2100 else None

    return None


def normalize_citations(raw):
    if raw is None:
        return 0

    if isinstance(raw, list):
        nums = [int(x) for x in raw if str(x).isdigit()]
        return nums[0] if len(nums) else 0

    if isinstance(raw, str):
        digits = re.findall(r'\d+', raw)
        return int(digits[0]) if digits else 0

    if isinstance(raw, (int, float)):
        return int(raw)

    return 0

def clean_title(title):
    if title is None:
        return None
    # Remove non-standard characters (防止被拆成多个 query 参数)
    title = re.sub(r'[^0-9A-Za-z\u4e00-\u9fa5 ,.:;?!()\-_/]+', ' ', title)
    # Normalize whitespace
    title = re.sub(r'\s+', ' ', title)
    return title.strip()

def clean_url(url):
    if url is None:
        return None
    if isinstance(url, str) and url.startswith("http"):
        return url.strip()
    return None

    
def query_result(key_word, year_start, year_end):
    """
    Send Google Scholar query using scholar.py and return list of articles.
    """

    try:
        querier = scholar.ScholarQuerier()
        settings = scholar.ScholarSettings()
        querier.apply_settings(settings)

        query = scholar.SearchScholarQuery()
        query.set_words(key_word)
        query.set_timeframe(year_start, year_end)
        query.set_num_page_results(40)
        query.set_scope(False)
        query.set_include_citations(False)
        query.set_include_patents(False)

        querier.send_query(query)

        return querier.articles

    except Exception as e:
        print("[ERROR] Scholar query exception:", e)
        return []

def SSSS(topic, sub_keyword_list, year_from, year_to, citation_threshold,
         number_of_searches_per_key_word_per_year=10, sleep_interval=360):
    """
    A robust version of SSSS with strong error handling.
    """

    import traceback

    # ---- Generate keyword combinations ----
    all_combination = list(itertools.product(*sub_keyword_list))
    key_words_list = [
        str(c).replace("'", "").replace("(", "").replace(")", "")
        for c in all_combination
    ]

    # ---- Prepare folder structure ----
    base_path = f"../results/topics/{topic}"
    os.makedirs(base_path, exist_ok=True)

    crossref_cols = ['doi','authors','issued','abstract','link','is_referenced_by_count']
    cols = ['title','num_citations','year','excerpt','url','url_pdf',
            'indicator','key_words'] + crossref_cols

    summary_path = f"{base_path}/summary.csv"

    if not os.path.exists(summary_path):
        summary_df = pd.DataFrame([], columns=cols)
        summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    else:
        summary_df = pd.read_csv(summary_path)

    completed_pairs = summary_df[['key_words', 'year']].drop_duplicates()

    total_keywords = len(key_words_list)
    total_years = year_to - year_from + 1

    print("Total keyword list:", key_words_list)
    print("Total keywords:", len(key_words_list))

    # ---- Helper to detect whether summary.csv is open ----
    def detect_file_open():
        try:
            os.rename(summary_path, summary_path + ".temp")
            os.rename(summary_path + ".temp", summary_path)
            return False
        except OSError:
            print("\n[WARNING] summary.csv is currently open. Please close it.\n")
            return True

    # ======================================================================
    # Main loops
    # ======================================================================
    for year_idx, year in enumerate(range(year_from, year_to + 1), start=1):

        for kw_idx, key_words in enumerate(key_words_list, start=1):

            # Already processed before?
            if ((completed_pairs.key_words == key_words) &
                (completed_pairs.year == year)).any():
                print(f"[SKIP] Already done → Year {year}, Keyword {key_words}")
                continue

            print("\n" + "=" * 80)
            print(f"Year {year} ({year_idx}/{total_years}), "
                  f"Keyword {kw_idx}/{total_keywords}")
            print(f"Running keyword: {key_words}")
            print("=" * 80)

            # ---- Google Scholar Query ----
            try:
                articles = query_result(key_words, year, year)
                print(f"> Number of fetched articles: {len(articles)}")
            except Exception as e:
                print("[ERROR] Google Scholar query failed:", e)
                traceback.print_exc()
                continue

            # If empty, require manual CAPTCHA
            while len(articles) == 0:
                print("\n[CAPTCHA REQUIRED] Please solve Google Scholar CAPTCHA…")
                input("Press ENTER after solving at: https://scholar.google.com\n")
                articles = query_result(key_words, year, year)
                print("> Retrying, fetched:", len(articles))

            # ======================================================================
            # Process articles
            # ======================================================================
            max_papers = min(len(articles), number_of_searches_per_key_word_per_year)

            for nth in range(max_papers):
                print(f"  Processing paper {nth+1} / {max_papers}")

                try:
                    article = articles[nth]

                    # ======== RAW FIELDS (may be list/dict/object) ========
                    raw_title     = article['title']
                    raw_year      = article['year']
                    raw_url       = article['url']
                    raw_pdf       = article['url_pdf']
                    raw_excerpt   = article['excerpt']
                    raw_citations = article['num_citations']

                    # ======== NORMALIZED (SAFE) FIELDS ========
                    title     = clean_title(normalize_field(raw_title))
                    excerpt   = normalize_field(raw_excerpt)
                    url       = clean_url(normalize_field(raw_url))
                    url_pdf   = clean_url(normalize_field(raw_pdf))
                    year_found = normalize_year(raw_year)
                    citations = normalize_citations(raw_citations)

                    # ======== DEBUG ========
                    print("    Cleaned Title:", title)
                    print("    Cleaned Year:", year_found)
                    print("    Cleaned Citations:", citations)
                    print("    Cleaned URL:", url)

                except Exception as e:
                    print(f"    [SKIP - PARSE ERROR] article #{nth+1}: {e}")
                    continue

                # ======== VALIDATION BEFORE CROSSREF ========
                if title is None or title.strip() == "":
                    print("    [SKIP] Invalid title")
                    continue

                if not isinstance(citations, int):
                    print("    [SKIP] Invalid citations:", citations)
                    continue

                if citations < citation_threshold:
                    print(f"    [SKIP] Citations {citations} < threshold {citation_threshold}")
                    continue

                if year_found is None:
                    print("    [SKIP] Invalid year:", raw_year)
                    continue

                if title in summary_df.title.values:
                    print("    [SKIP] Duplicate title")
                    continue

                # ======== CROSSREF LOOKUP (SAFE) ========
                try:
                    meta = lookup_metadata(title, year=year_found)
                except Exception as e:
                    print("    [WARNING] Crossref lookup failed:", e)
                    meta = {}

                # ======== SAVE TO CSV ========
                while detect_file_open():
                    print("Locked! Waiting...")
                    time.sleep(2)

                new_row = pd.DataFrame([[
                    title,
                    citations,
                    year_found,
                    excerpt,
                    url,
                    url_pdf,
                    0,
                    key_words,
                    meta.get('doi'),
                    meta.get('authors'),
                    meta.get('issued'),
                    meta.get('abstract'),
                    meta.get('link'),
                    meta.get('is_referenced_by_count')
                ]], columns=cols)

                summary_df = pd.concat([summary_df, new_row], ignore_index=True)
                summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')
                print("    [SAVED]")

            # ======================================================================
            # Sleep to avoid Scholar blocking
            # ======================================================================
            delay = sleep_interval + random() * 60
            print(f"Sleeping {delay:.1f} seconds...\n")
            time.sleep(delay)
