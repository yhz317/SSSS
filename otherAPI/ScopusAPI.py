import itertools
import requests
import pandas as pd
from time import sleep

# ----------------------------
# 配置区域
# ----------------------------

API_KEY = "fa834a18064f7577706228fd4f519148"   # ←←← 填你的 Scopus API Key
RESULTS_PER_QUERY = 25            # 每个组合返回多少篇
OUTPUT_FILE = "scopus_results.csv"

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

# 关键词列表
keyword_lists = [sub_keyword_list1,sub_keyword_list2]

# ----------------------------
# 生成关键词排列组合
# ----------------------------
def generate_queries(keyword_lists):
    combinations = list(itertools.product(*keyword_lists))
    queries = [" AND ".join(combo) for combo in combinations]
    return queries

# ----------------------------
# 调用 Scopus API
# ----------------------------
def scopus_search(query, count):
    url = "https://api.elsevier.com/content/search/scopus"
    params = {"query": query, "apiKey": API_KEY, "count": count}

    response = requests.get(url, params=params)
    data = response.json()

    entries = data.get("search-results", {}).get("entry", [])
    results = []

    for e in entries:
        results.append({
            "query": query,
            "title": e.get("dc:title", ""),
            "authors": e.get("dc:creator", ""),
            "publication": e.get("prism:publicationName", ""),
            "date": e.get("prism:coverDate", ""),
            "doi": e.get("prism:doi", ""),
            "citations": e.get("citedby-count", "0"),
            "link": e.get("link", [{}])[0].get("@href", "")
        })
    return results

# ----------------------------
# 主程序
# ----------------------------
def main():
    queries = generate_queries(keyword_lists)
    print(f"共生成 {len(queries)} 个检索组合：")
    for q in queries:
        print(" -", q)

    all_results = []

    print("\n开始检索...\n")
    for q in queries:
        print(f"检索：{q}")
        try:
            results = scopus_search(q, RESULTS_PER_QUERY)
            all_results.extend(results)
        except Exception as e:
            print(f"请求失败：{e}")
        sleep(1)  # 防止请求过快被限制

    # 导出 CSV
    df = pd.DataFrame(all_results)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\n检索完成！共获取 {len(df)} 条文献。")
    print(f"结果已导出到：{OUTPUT_FILE}")

# ----------------------------
# 执行
# ----------------------------
if __name__ == "__main__":
    main()
