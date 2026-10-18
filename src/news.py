import json, os, re, feedparser, trafilatura
from config import FEEDS
USED = "used.json"

def _used():
    return set(json.load(open(USED))) if os.path.exists(USED) else set()

def mark_used(link):
    u = _used(); u.add(link); json.dump(sorted(u), open(USED, "w"))

def candidates(n=12):
    used, items = _used(), []
    for url in FEEDS:
        for e in feedparser.parse(url).entries[:8]:
            if e.link not in used:
                items.append({"title": re.sub(r"\s+-\s+[^-]+$", "", e.title),
                              "link": e.link,
                              "summary": re.sub("<[^>]+>", "", e.get("summary", ""))})
    return items[:n]

def fetch_text(item):
    try:
        t = trafilatura.extract(trafilatura.fetch_url(item["link"])) or ""
    except Exception:
        t = ""
    return (t or item["summary"])[:3500]
