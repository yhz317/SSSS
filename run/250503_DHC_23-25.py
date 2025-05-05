from SSSS.base import SSSS
import numpy as np
import os
from pathlib import Path

# 1. Find the script’s own location
script_path = Path(__file__).resolve()      # e.g. C:\…\GitHub\SSSS\run\myscript.py
script_dir  = script_path.parent            # e.g. C:\…\GitHub\SSSS\run

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
'district thermal',
'district energy',
'district heat pump',
'thermal grid'
]

sub_keyword_list = [sub_keyword_list1, sub_keyword_list2]

topic = '250503_DHC_23-25'
citation_threshold = 0
number_of_searches_per_key_word_per_year = 20
year_interval = 1
sleep_interval = 60

for year in np.arange(2023, 2026, year_interval):
    print("Year:", year)
    year_from = year
    year_to = year + year_interval - 1
    citation_threshold = int(max(0,(2025 - year)))
    SSSS(topic, sub_keyword_list, year_from, year_to, citation_threshold, number_of_searches_per_key_word_per_year, sleep_interval)
