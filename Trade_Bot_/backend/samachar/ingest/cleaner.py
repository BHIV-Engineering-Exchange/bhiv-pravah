import re
from bs4 import BeautifulSoup
from langdetect import detect

def clean_text(text):
    html = text or ""
    soup = BeautifulSoup(html, "html.parser")
    plain = soup.get_text(" ")
    norm = re.sub(r"\s+", " ", plain).strip()
    return norm

def detect_language(text):
    try:
        return detect(text or "")
    except Exception:
        return "unknown"

def clean_article(article):
    a = dict(article or {})
    a["title"] = clean_text(a.get("title"))
    a["summary"] = clean_text(a.get("summary"))
    a["language"] = detect_language((a.get("title") or "") + " " + (a.get("summary") or ""))
    return a