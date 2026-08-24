from SSSS.base import SSSS
import os
from pathlib import Path

# Find the script's own location and run relative to the repository's run dir.
script_path = Path(__file__).resolve()
script_dir = script_path.parent

# 2. Change CWD to that folder
os.chdir(script_dir)

# (optional) verify
# print("CWD now =", os.getcwd())

sub_keyword_list1 = [
    '4th generation',
    '5th generation',
    'fifth generation',
    'fourth generation',
    'bi-directional',
    'bidirectional',
    'low temperature',
    'low-temperature',
    'ultra-low temperature',
]

sub_keyword_list2 = [
    'district heating and cooling',
    # 'district thermal',
    # 'district energy',
    # 'district heat pump',
    # 'thermal network',
    # 'thermal grid',
]

sub_keyword_list = [sub_keyword_list1, sub_keyword_list2]

# Keep the topic name aligned with the existing results directory and the
# downstream filtering/PDF/Zotero scripts.
topic = '251209_DHC_23-25'

citation_threshold = 0
number_of_searches_per_key_word_per_year = 20
latest_year = 2025
earliest_year = 2020
year_interval = -1
sleep_interval = 0

# Search each year from 2025 down through 2020, inclusive.
for year in range(latest_year, earliest_year - 1, year_interval):
    print("Year:", year)
    year_from = year
    year_to = year
    # citation_threshold = int(max(0,(2025 - year)))
    citation_threshold = 0
    SSSS(
        topic,
        sub_keyword_list,
        year_from,
        year_to,
        citation_threshold,
        number_of_searches_per_key_word_per_year,
        sleep_interval,
        skip_completed=False,  # 强制重跑全部（即使 summary.csv 里已有）
    )
