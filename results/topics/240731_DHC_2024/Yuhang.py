from SSSS.base import SSSS
import numpy as np

topic = '240731_DHC_2024'
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
'district energy',
'district heat pump',
'thermal grid',
]
sub_keyword_list = [sub_keyword_list1, sub_keyword_list2]
citation_threshold = 0
number_of_searches_per_key_word_per_year = 20
sleep_interval = 90
year_interval = 1

for year in np.arange(2023, 2024, year_interval):
    print("Year:", year)
    year_from = year
    year_to = year + year_interval - 1
    # citation_threshold = int((2023 - year)/2)
    SSSS(topic, sub_keyword_list, year_from, year_to, citation_threshold, number_of_searches_per_key_word_per_year, sleep_interval)
