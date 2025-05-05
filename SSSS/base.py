import time
import SSSS.scholar as scholar
import pandas as pd
import numpy as np
import os
from random import random
import itertools
import requests

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
    resp = requests.get('https://api.crossref.org/works', params=params)
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
    resp = requests.get('https://api.crossref.org/works', params=params)
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
    
def SSSS(topic, sub_keyword_list, year_from, year_to, citation_threshold, number_of_searches_per_key_word_per_year = 10, sleep_interval = 360):
    """
    The function conducts SSSS as introduced in the journal paper: XXX.

    :param topic: string; the topic of this search. The searched result Will be saved as summary.csv in results/topics/[topic]
    :param sub_keyword_list: list of list of strings; defines the sub-keyword list of SSSS, example: [['energy','gas'],['prediction', 'forecasting'], ['in buildings', 'HVAC']]
    :param year_from: int; limit start year of search
    :param year_to: int; limit end year of search
    :param citation_threshold: int; limit the minimum citation number of searched papers
    :param number_of_searches_per_key_word_per_year: int; number of paper crawled from each keyword seasrch
    :param sleep_interval: float; seconds that is setted between each search
    """
    # print("CWD =", os.getcwd())
    
    # generate keyword list from sub-keyword list
    all_combination = list(itertools.product(*sub_keyword_list))
    key_words_list = []
    for i in range(len(all_combination)):
        key_words_list += [str(all_combination[i]).replace("'", "").replace('(','').replace(')','')]

    def query_result(key_word, year_start, year_end):

        querier = scholar.ScholarQuerier()
        settings = scholar.ScholarSettings()
        querier.apply_settings(settings)

        query = scholar.SearchScholarQuery()
        #query.set_author("Liang Zhang")
        query.set_words(key_word)
        query.set_timeframe(year_start,year_end)
        query.set_num_page_results(40)
        query.set_scope(False)
        #query.set_scope(True)
        query.set_include_citations(False)
        query.set_include_patents(False)

        querier.send_query(query)

        return querier.articles

    def detect_file_open():
        try:
            os.rename('../results/topics/{}/summary.csv'.format(topic), '../results/topics/{}/temp_summary.csv'.format(topic))
            os.rename('../results/topics/{}/temp_summary.csv'.format(topic), '../results/topics/{}/summary.csv'.format(topic))
        except OSError:
            print("\n**********************************************************\nsummary.csv is detected to be open. Please close the summary.csv before continuing...\n********************************************************** ")

    # Create folder structure
    if not os.path.isdir("../results/"):
        os.mkdir('../results/')

    if not os.path.isdir("../results/topics/"):
        os.mkdir('../results/topics/')

    if not os.path.isdir("../results/topics/{}/".format(topic)):
        os.mkdir('../results/topics/{}/'.format(topic))
        
    crossref_cols = ['doi','authors','issued','abstract','link','is_referenced_by_count']
    cols = ['title', 'num_citations', 'year', 'excerpt', 'url', 'url_pdf','indicator','key_words'] + crossref_cols
    # define the summary dataframe
    if not os.path.exists('../results/topics/{}/summary.csv'.format(topic)):
        # crossref_cols = ['doi']
        summary_df = pd.DataFrame([],columns = cols)
        summary_df.to_csv('../results/topics/{}/summary.csv'.format(topic), index = None, header = summary_df.columns)
    else:
        summary_df = pd.read_csv('../results/topics/{}/summary.csv'.format(topic))

    # detect whether the summary.csv file is open
    #    detect_file_open()

    # get all the inputs
    #input_string = input("Enter key words separated by semicolumn: ")
    #input_string = final_key_word_list
    #key_words_list  = list(set(input_string.split(";")))
    print('Total keyword list: {}'.format(key_words_list))
    print('Total number of keywords is: {}'.format(len(key_words_list)))
    #year_from = int(input("Year From: "))
    #year_to = int(input("Year To: "))
    #citation_threshold = int(input("Citation_threshold: "))

    #number_of_searches_per_key_word_per_year = int(input("Enter number of searches per key word per year (int, less than or equal to 20):"))

    # modified keyword list
    completed_keyword_list = summary_df.key_words.unique().tolist()[0:-1]
    key_words_list = list(set(key_words_list) - set(completed_keyword_list))
    print('Total keyword list for this run: {}'.format(key_words_list))
    print('The number of keywords for this run: {}'.format(len(key_words_list)))
    
    for key_words in key_words_list:
        
        print(key_words)        
        articles = query_result(key_words, year_from, year_to)
        print("Number of fetched articles:", len(articles))
        
        while len(articles) == 0:
            temp = input('Please enter 1 after completing the anti-robot test at https://scholar.google.com/scholar?hl=en&as_sdt=0%2C6&q=test&btnG=')
            
            articles = query_result(key_words, year_from, year_to)
            print(len(articles))
            if len(articles) != 0:
                break
            
        for nth_paper in range(min(len(articles),number_of_searches_per_key_word_per_year)):
            title_nth = articles[nth_paper]['title']
            num_citations_nth = articles[nth_paper]['num_citations']
            year_nth = articles[nth_paper]['year']
            excerpt_nth = articles[nth_paper]['excerpt']
            if articles[nth_paper]['url'][0:25] == 'http://scholar.google.com':
                url_nth = articles[nth_paper]['url'][26:]
            else:
                url_nth = articles[nth_paper]['url']
            url_pdf_nth = articles[nth_paper]['url_pdf']
            
            # # NEW: fetch DOI
            # doi_nth = lookup_doi(title_nth, year=year_nth)
            # time.sleep(1) # add a 1 s pause between Crossref calls (to be a good API citizen)
            # NEW: fetch full metadata (incl. DOI, authors, date, abstract, link, cited‑by)
            meta = lookup_metadata(title_nth, year=year_nth)
            time.sleep(1)

            if (title_nth not in summary_df.title.tolist()) & (num_citations_nth >= citation_threshold):
                detect_file_open()
                #indicator_nth = int(input("\nEnter Indicator, 0 means bad paper, 1 means good paper:\n\nTitle: {}\nCitation: {}\nYear: {}\nAbstract: {}\nurl: {}\nurl_pdf: {}\n".format(title_nth,num_citations_nth,year_nth,excerpt_nth, url_nth, url_pdf_nth)))
                indicator_nth = 0
                # build row including all new metadata fields
                df_nth = pd.DataFrame([[title_nth, num_citations_nth, year_nth, excerpt_nth, url_nth, url_pdf_nth, indicator_nth, key_words,
                                    meta.get('doi'),
                                    meta.get('authors'),
                                    meta.get('issued'),
                                    meta.get('abstract'),
                                    meta.get('link'),
                                    meta.get('is_referenced_by_count')
                                    ]], columns=cols)
                # use concat instead of append
                summary_df = pd.concat([summary_df, df_nth], ignore_index=True)
                # make sure that summary.csv file is closed
                summary_df.to_csv('../results/topics/{}/summary.csv'.format(topic), 
                                index = False,
                                encoding='utf-8-sig'    # <-- UTF‑8 with BOM)
                                )
        
        random_sleep_interval = sleep_interval + random()*60
        print('sleep for {}+ seconds'.format(random_sleep_interval))
        time.sleep(random_sleep_interval)