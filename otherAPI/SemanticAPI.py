import os
import time
import itertools
import requests
import pandas as pd
from random import random

# ===============================
# Semantic Scholar 查询函数
# ===============================
def ss_search(query, year_from, year_to, limit=20, max_retries=5):
    """
    使用 Semantic Scholar API 搜索论文，包含自动重试和限速机制。
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,authors,year,abstract,citationCount,externalIds,url"
    }
    
    for retry in range(max_retries):
        try:
            r = requests.get(url, params=params)
            
            # 如果成功，正常返回
            if r.status_code == 200:
                data = r.json().get("data", [])
                data = [p for p in data if p.get("year") and year_from <= p["year"] <= year_to]
                return data
            
            # 如果是 429，说明请求太快 → 等待一段时间重试
            if r.status_code == 429:
                wait = 3 + retry * 3  # 3s, 6s, 9s, 12s, ...
                print(f"⚠️  Semantic Scholar 请求过快(429)，等待 {wait} 秒后重试...")
                time.sleep(wait)
                continue
            
            # 如果是其它错误，抛出异常
            r.raise_for_status()

        except Exception as e:
            print(f"请求出错（第 {retry+1} 次）, 错误：{e}")
            time.sleep(2 + retry)
    
    print("❌ 多次重试失败，返回空结果。")
    return []



# ===============================
# Crossref 元数据查询（可选）
# ===============================
def lookup_metadata(doi):
    """
    通过 DOI 获取 Crossref 元数据。
    """
    if doi is None:
        return {}
    
    url = f"https://api.crossref.org/works/{doi}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        item = resp.json().get("message", {})
    except:
        return {}

    authors = item.get("author", [])
    authors = "; ".join([
        f"{a.get('given','')} {a.get('family','')}".strip()
        for a in authors
    ])

    issued = None
    try:
        parts = item.get("issued", {}).get("date-parts", [[]])[0]
        issued = "-".join(str(p) for p in parts)
    except:
        issued = None
    
    return {
        "cr_authors": authors,
        "cr_issued": issued,
        "cr_link": item.get("URL"),
        "cr_reference_count": item.get("is-referenced-by-count")
    }


# ===============================
# 重写后的 SSSS
# ===============================
def SSSS(topic, sub_keyword_list, year_from, year_to, citation_threshold, limit_per_keyword=20, sleep_interval=10):
    
    # 生成关键词组合
    combinations = list(itertools.product(*sub_keyword_list))
    keyword_list = [
        " ".join(combo).replace(" ,", ",").strip()
        for combo in combinations
    ]
    
    print("关键词组合数量:", len(keyword_list))
    
    # 输出目录
    outdir = f"../results/topics/{topic}/"
    os.makedirs(outdir, exist_ok=True)

    cols = [
        "title","year","citationCount","authors","abstract","url","doi",
        "keyword",
        "cr_authors","cr_issued","cr_link","cr_reference_count"
    ]

    csv_path = os.path.join(outdir, "summary.csv")
    if not os.path.exists(csv_path):
        df = pd.DataFrame([], columns=cols)
        df.to_csv(csv_path, index=False)
    else:
        df = pd.read_csv(csv_path)

    # 已处理过的关键词用于跳过
    completed_keywords = df.keyword.unique().tolist()

    for key in keyword_list:
        if key in completed_keywords:
            print(f"跳过已完成关键词：{key}")
            continue

        print(f"\n====== 搜索关键词：{key} ======")

        papers = ss_search(key, year_from, year_to, limit=limit_per_keyword)
        print("获取论文数量:", len(papers))

        for p in papers:

            title = p.get("title")
            year = p.get("year")
            cites = p.get("citationCount", 0)
            abstract = p.get("abstract")
            url = p.get("url")
            doi = None
            if p.get("externalIds"):
                doi = p["externalIds"].get("DOI")

            authors = "; ".join(a["name"] for a in p.get("authors", []))

            # 过滤：引用次数不达标
            if cites < citation_threshold:
                continue

            # 过滤：重复论文
            if title in df.title.tolist():
                continue

            # Crossref 元数据（可选）
            meta = lookup_metadata(doi)
            time.sleep(0.5)

            row = {
                "title": title,
                "year": year,
                "citationCount": cites,
                "authors": authors,
                "abstract": abstract,
                "url": url,
                "doi": doi,
                "keyword": key,
                **meta
            }

            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        # 随机 sleep 防止 API 速率限制
        wait = sleep_interval + random()*3
        print(f"等待 {wait:.2f} 秒...\n")
        time.sleep(wait)

    print("🎉 SSSS 搜索完成！数据已写入：", csv_path)

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
'thermal network',
'thermal grid',
]

SSSS(
    topic="Semantic_DHC",
    sub_keyword_list=[sub_keyword_list1,sub_keyword_list2],
    year_from=2020,
    year_to=2026,
    citation_threshold=0
)