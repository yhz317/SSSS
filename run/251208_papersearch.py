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
    "embodied carbon",
    "whole life carbon",
    "life cycle assessment",
    "life cycle greenhouse gas emissions",
    "upfront embodied carbon",
    "cradle to completion",
    "cradle to gate",
    "replacement embodied carbon",
    "environmental product declaration"
]

sub_keyword_list2 = [
    "MEP",
    "mechanical electrical plumbing systems",
    "HVAC",
    "heating ventilation and air conditioning",
    "plumbing",
    "electrical system",
    "ventilation",
    "lighting",
    "building management system"
]


sub_keyword_list = [sub_keyword_list1, sub_keyword_list2]

topic = '251208_papersearch'
citation_threshold = 0
number_of_searches_per_key_word_per_year = 20
year_interval = 1
sleep_interval = 60

# for year in np.arange(2015, 2026, year_interval):

year_from = 2000
year_to = 2025
# citation_threshold = int(max(0,(2025 - year)))
citation_threshold = 0
SSSS(topic, sub_keyword_list, year_from, year_to, citation_threshold, number_of_searches_per_key_word_per_year, sleep_interval)
