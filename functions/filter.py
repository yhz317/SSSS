import pandas as pd
import re

# =========================================================
# Helper functions
# =========================================================

def contains_whole_word(text: str, word: str) -> bool:
    return re.search(rf'\b{re.escape(word.lower())}\b', text) is not None


def title_contains_excluded(title: str,
                            substring_exclude,
                            whole_word_exclude):
    title = title.lower()

    for k in substring_exclude:
        if k.lower() in title:
            return f"substring_exclude: {k}"

    for k in whole_word_exclude:
        if contains_whole_word(title, k):
            return f"whole_word_exclude: {k}"

    return None


# =========================================================
# Main filter function
# =========================================================

def filter_summary(
    input_csv,
    output_csv,
    year_now=2025,

    title_must_have=None,
    title_exclude_substring=None,
    title_exclude_whole_word=None,

    min_citation_density=0.0,
    drop_indicator_values=(-1,),

    VERBOSE=True,           # 👈 开关
    MAX_PRINT=1000            # 👈 最多打印多少条
):

    df = pd.read_csv(input_csv)
    keep_rows = []

    removed = []   # 存 (reason, title)

    for _, row in df.iterrows():

        raw_title = row.get('title')

        # -------------------------------------------------
        # PRE-CHECK: empty title
        # -------------------------------------------------
        if pd.isna(raw_title) or str(raw_title).strip() == '':
            removed.append(("empty_title", raw_title))
            continue

        title = str(raw_title).strip().lower()

        year = row.get('year')
        citations = row.get('num_citations', 0)
        indicator = row.get('indicator', 0)

        # -------------------------------------------------
        # 0. Manual exclusion
        # -------------------------------------------------
        if indicator in drop_indicator_values:
            removed.append(("manual_exclude", title))
            continue

        # -------------------------------------------------
        # 1. Title MUST HAVE (OR)
        # -------------------------------------------------
        if title_must_have:
            if not any(k.lower() in title for k in title_must_have):
                removed.append(("missing_must_have", title))
                continue

        # -------------------------------------------------
        # 2. Title MUST NOT HAVE
        # -------------------------------------------------
        reason = title_contains_excluded(
            title,
            substring_exclude=title_exclude_substring or [],
            whole_word_exclude=title_exclude_whole_word or []
        )
        if reason:
            removed.append((reason, title))
            continue

        # -------------------------------------------------
        # 3. Citation density
        # -------------------------------------------------
        try:
            age = max(1, year_now - int(year))
            citation_density = citations / age
        except Exception:
            citation_density = 0

        if citation_density < min_citation_density:
            removed.append(("low_citation_density", title))
            continue

        keep_rows.append(row)

    # -------------------------------------------------
    # Save kept papers
    # -------------------------------------------------
    filtered_df = pd.DataFrame(keep_rows)
    filtered_df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print(f"[DONE] {len(filtered_df)} / {len(df)} papers kept")

    # -------------------------------------------------
    # Print removed titles
    # -------------------------------------------------
    if VERBOSE:
        print("\n[REMOVED TITLES]")
        for i, (reason, title) in enumerate(removed[:MAX_PRINT], 1):
            print(f"{i:03d}. [{reason}] {title}")

        if len(removed) > MAX_PRINT:
            print(f"... ({len(removed) - MAX_PRINT} more not shown)")

    return filtered_df, removed


# =========================================================
# Configuration (YOUR CASE)
# =========================================================

TITLE_MUST_HAVE = [
    'district',
    'heating','cooling','thermal',
    'network', 'loop', 'grid',
    'ambient','geothermal',
    'heat pump'
]

# Long, unambiguous terms → substring match
TITLE_EXCLUDE_SUBSTRING = [
    'wireless',
    'communication',
    'battery','batteries',
    'quantum',
    'semiconductor',
    'laser',
    'Magnet',
    'capacitor',
    'ultrasonic',
    'motor','polyimide','ceramic',
    'charging','charger',
    'conductive','microwave','conduction',
    'conductivity','wavelet','fiber','thermalization','nanoscale','nano','SiC','nanofluid','converter',
    'photon','composite','vacuum',' ultra-low pressure',
    'cryogenic','combustor','lithium','magnet','Wavelength','superalloy','Crystal','fatigue','reactor','synchrotron',
    'steel','Assembly','phonon','decomposition','Freezer','Molecular','deformation','salt',
    'decomposition','Fuel cell','Turbine','spindle',
    'copper','alloy','electron','corrosion','bi-directional long short-term memory','modality',
    'Hydrogen','distillation','thermoelectric','Aerodynamic'
    'moisture','combustion','granite','ultra-low load','ultra-low energy','ultra-low emission',
    'metallic','polymer', 'deterioration','Radio',
    'Ultrasound','voltage','subsurface','circuit','Bi-directional power','bidirectional long',
    'AC/DC',
    'bidirectional fusion network','bidirectional electric vehicle','Elastomer',
    'automotive','electric machine','recurrent','Grid Array','reaction network',
    'oxidation'
]

# Short / risky terms → whole-word match ONLY
TITLE_EXCLUDE_WHOLE_WORD = [
    'sic',        # avoid killing "basic / physics / classic"
    'metal','FGM','IGBT','RGB','ball',
]

# =========================================================
# Run
# =========================================================

# input_csv = r'D:\Github\SSSS\results\topics\251209_DHC_23-25\summary.csv'
input_csv = r'D:\Github\SSSS\results\topics\251209_DHC_23-25\summary_filteredv3.csv'
output_csv = r'D:\Github\SSSS\results\topics\251209_DHC_23-25\summary_filteredv3.csv'

filtered_df, removed = filter_summary(
    input_csv=input_csv,
    output_csv=output_csv,

    title_must_have=TITLE_MUST_HAVE,
    title_exclude_substring=TITLE_EXCLUDE_SUBSTRING,
    title_exclude_whole_word=TITLE_EXCLUDE_WHOLE_WORD,

    min_citation_density=0.0  # disable citation filtering
)

# removed_df = pd.DataFrame(removed, columns=["reason", "title"])
# removed_df.to_csv("removed_titles.csv", index=False)

# 统计各类删除原因
# from collections import Counter
# print(Counter(r for r, _ in removed))