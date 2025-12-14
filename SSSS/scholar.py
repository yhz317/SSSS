#! /usr/bin/env python
"""
Final compatible scholar.py
- No PDF parsing
- Keeps ALL legacy interfaces as stubs
- Safe for existing base.py without modification
"""

import os
import re
import sys
import warnings



try:
    from urllib.request import HTTPCookieProcessor, Request, build_opener
    from urllib.parse import quote, unquote
    from http.cookiejar import MozillaCookieJar
except ImportError:
    from urllib2 import Request, build_opener, HTTPCookieProcessor
    from urllib import quote, unquote
    from cookielib import MozillaCookieJar

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup is required.")
    sys.exit(1)

# ----------------------------------------------------------------------
# Compatibility helpers
# ----------------------------------------------------------------------
if sys.version_info[0] == 3:
    unicode = str
    encode = lambda s: unicode(s)
else:
    def encode(s):
        if isinstance(s, basestring):
            return s.encode("utf-8")
        return str(s)

# ----------------------------------------------------------------------
# Errors
# ----------------------------------------------------------------------
class Error(Exception):
    pass

class FormatError(Error):
    pass

class QueryArgumentError(Error):
    pass

# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------
class ScholarConf(object):
    VERSION = "2.10-compatible"
    LOG_LEVEL = 1
    MAX_PAGE_RESULTS = 10
    SCHOLAR_SITE = "http://scholar.google.com"
    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64; rv:27.0) "
        "Gecko/20100101 Firefox/27.0"
    )
    COOKIE_JAR_FILE = "SCHOLAR_COOKIE_FILE.txt"

# ----------------------------------------------------------------------
# Utils
# ----------------------------------------------------------------------
class ScholarUtils(object):
    LOG_LEVELS = {"error":1, "warn":2, "info":3, "debug":4}

    @staticmethod
    def ensure_int(arg, msg=None):
        try:
            return int(arg)
        except Exception:
            raise FormatError(msg)

    @staticmethod
    def log(level, msg):
        if level not in ScholarUtils.LOG_LEVELS:
            return
        if ScholarUtils.LOG_LEVELS[level] > ScholarConf.LOG_LEVEL:
            return
        sys.stderr.write(f"[{level.upper():5}] {msg}\n")
        sys.stderr.flush()

# ----------------------------------------------------------------------
# Article model
# ----------------------------------------------------------------------
class ScholarArticle(object):
    def __init__(self):
        self.attrs = {
            "title":         [None, "Title", 0],
            "url":           [None, "URL", 1],
            "year":          [None, "Year", 2],
            "num_citations": [0,    "Citations", 3],
            "cluster_id":    [None, "Cluster ID", 4],
            "excerpt":       [None, "Excerpt", 5],
        }

    def __getitem__(self, key):
        return self.attrs.get(key, [None])[0]

    def __setitem__(self, key, value):
        if key in self.attrs:
            self.attrs[key][0] = value

# ----------------------------------------------------------------------
# Parser (single, stable)
# ----------------------------------------------------------------------
class ScholarArticleParser(object):
    def __init__(self, site=None):
        self.site = site or ScholarConf.SCHOLAR_SITE
        self.year_re = re.compile(r"\b(?:19|20)\d{2}\b")

    def parse(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for div in soup.find_all("div", class_="gs_r"):
            art = self._parse_article(div)
            if art and art["title"]:
                self.handle_article(art)

    def handle_article(self, article):
        pass

    def _parse_article(self, div):
        art = ScholarArticle()

        # Title + URL
        h3 = div.find("h3", class_="gs_rt")
        if h3:
            a = h3.find("a")
            if a:
                # exact equivalent of: ''.join(tag.h3.findAll(text=True))
                texts = a.find_all(string=True)
                art["title"] = "".join(texts)
                art["url"] = self._path2url(a.get("href"))

        # Meta (authors + year)
        meta = div.find("div", class_="gs_a")
        if meta:
            years = self.year_re.findall(meta.get_text())
            if years:
                art["year"] = years[0]

        # Footer links
        footer = div.find("div", class_="gs_fl")
        if footer:
            for a in footer.find_all("a"):
                href = a.get("href", "")
                text = a.get_text()
                if href.startswith("/scholar?cites") and text.startswith("Cited by"):
                    art["num_citations"] = int(text.split()[-1])
                    art["cluster_id"] = self._extract_cluster_id(href)

        # Excerpt
        rs = div.find("div", class_="gs_rs")
        if rs:
            art["excerpt"] = " ".join(rs.stripped_strings)

        return art

    def _path2url(self, path):
        if not path:
            return None
        if path.startswith("http"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return self.site + path

    def _extract_cluster_id(self, href):
        m = re.search(r"cites=(\d+)", href)
        return m.group(1) if m else None

# ----------------------------------------------------------------------
# Queries
# ----------------------------------------------------------------------
class ScholarQuery(object):
    def __init__(self):
        self.num_results = None

    def set_num_page_results(self, n):
        self.num_results = ScholarUtils.ensure_int(n)

class SearchScholarQuery(ScholarQuery):
    URL = (
        ScholarConf.SCHOLAR_SITE + "/scholar?"
        "as_q=%(words)s&"
        "as_ylo=%(ylo)s&"
        "as_yhi=%(yhi)s&"
        "hl=en%(num)s"
    )

    def __init__(self):
        super().__init__()
        self.words = ""
        self.ylo = ""
        self.yhi = ""

    # ====== methods you ACTUALLY use ======
    def set_words(self, words):
        self.words = words or ""

    def set_timeframe(self, start, end):
        self.ylo = start or ""
        self.yhi = end or ""

    # ====== legacy compatibility stubs ======
    def set_scope(self, *args, **kwargs): pass
    def set_include_patents(self, *args, **kwargs): pass
    def set_include_citations(self, *args, **kwargs): pass
    def set_author(self, *args, **kwargs): pass
    def set_pub(self, *args, **kwargs): pass
    def set_phrase(self, *args, **kwargs): pass
    def set_words_some(self, *args, **kwargs): pass
    def set_words_none(self, *args, **kwargs): pass

    def get_url(self):
        args = {
            "words": quote(encode(self.words)),
            "ylo": self.ylo,
            "yhi": self.yhi,
            "num": f"&num={self.num_results}" if self.num_results else "",
        }
        return self.URL % args

# ----------------------------------------------------------------------
# ScholarSettings (compatibility stub)
# ----------------------------------------------------------------------
class ScholarSettings(object):
    def __init__(self):
        pass
    def is_configured(self):
        return False

# ----------------------------------------------------------------------
# Querier
# ----------------------------------------------------------------------
class ScholarQuerier(object):
    class Parser(ScholarArticleParser):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent
        def handle_article(self, article):
            self.parent.articles.append(article)

    def __init__(self):
        self.articles = []
        self.cjar = MozillaCookieJar()
        if os.path.exists(ScholarConf.COOKIE_JAR_FILE):
            try:
                self.cjar.load(ScholarConf.COOKIE_JAR_FILE, ignore_discard=True)
            except:
                pass
        self.opener = build_opener(HTTPCookieProcessor(self.cjar))

    # legacy no-op
    def apply_settings(self, settings):
        return True

    def send_query(self, query):
        self.articles = []
        url = query.get_url()
        html = self._get(url)
        if html:
            parser = self.Parser(self)
            parser.parse(html)

    def _get(self, url):
        try:
            ScholarUtils.log("info", f"requesting {unquote(url)}")
            req = Request(url, headers={"User-Agent": ScholarConf.USER_AGENT})
            with self.opener.open(req) as h:
                return h.read()
        except Exception as e:
            ScholarUtils.log("warn", f"request failed: {e}")
            return None
