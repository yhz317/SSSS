from SSSS.base import SSSS
import numpy as np

# topic = '240808_HP_TES_2013TO2023'

# topic = '240808_HP_TES_2024'

topic = '250312_HP_TES_MPC_2021TO2024'
sub_keyword_list1 = [
'heat pump',
    # 'chiller'
]

sub_keyword_list2 = [
'thermal energy storage',
#'phase change material',
    # 'demand response',
    # 'demand side management',
]
sub_keyword_list3 = ['model predictive control']

sub_keyword_list = [sub_keyword_list1, sub_keyword_list2,sub_keyword_list3]
citation_threshold = 0

number_of_searches_per_key_word_per_year = 20

sleep_interval = 90

year_interval = 1

for year in np.arange(2021, 2026, year_interval):
    print("Year:", year)
    year_from = year
    year_to = year + year_interval - 1
    # citation_threshold = int((2023 - year)/2)
    SSSS(topic, sub_keyword_list, year_from, year_to, citation_threshold, number_of_searches_per_key_word_per_year, sleep_interval)

