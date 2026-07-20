import os
import uuid
import requests
from datetime import datetime, timezone

def fetch_newsdata(query, language="en", page_size=10):
    """
    Fetch news from NewsData.io API and return structured, contract-ready items.
    All items include mandatory source tagging and normalized fields.
    """
    key = os.environ.get("NEWSDATA_API_KEY")
    if not key:
        return []
    
    url = "https://newsdata.io/api/1/news"
    params = {"apikey": key, "q": query, "language": language, "page": 1}
    to = float(os.environ.get("HTTP_TIMEOUT_SECONDS", "20"))
    
    try:
        r = requests.get(url, params=params, timeout=to)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[NewsData] Fetch failed: {e}")
        return []
    
    results = data.get("results", [])[:page_size]
    items = []
    
    for item in results:
        # Extract and normalize fields
        title = (item.get("title") or "").strip()
        content = (item.get("content") or item.get("description") or "").strip()
        link = (item.get("link") or "").strip()
        source_name = (item.get("source_id") or item.get("creator", ["NewsData"])[0] if isinstance(item.get("creator"), list) else "NewsData").strip()
        published = item.get("pubDate", "")
        
        # Skip items without essential data
        if not title and not content:
            continue
        
        # Generate deterministic ID
        item_id = item.get("article_id") or link or str(uuid.uuid4())
        
        # Normalize timestamp to ISO 8601
        timestamp = _normalize_timestamp(published)
        
        items.append({
            "id": item_id,
            "timestamp": timestamp,
            "source": source_name,
            "source_url": link,
            "title": title,
            "content": content,
            "link": link,
            "published": published,
            "_ingestion_method": "newsdata_api",
            "_query": query,
            "_language": language,
            "_category": item.get("category", ""),
            "_country": item.get("country", "")
        })
    
    return items

def _normalize_timestamp(published_str):
    """Convert API timestamp to ISO 8601 UTC format."""
    if not published_str:
        return datetime.now(timezone.utc).isoformat()
    
    try:
        from dateutil import parser as dparser
        dt = dparser.parse(published_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()