import os
import uuid
import requests
from datetime import datetime, timezone

def fetch_gnews(query, lang="en", max_results=10):
    """
    Fetch news from GNews API and return structured, contract-ready items.
    All items include mandatory source tagging and normalized fields.
    """
    token = os.environ.get("GNEWS_API_KEY")
    if not token:
        return []
    
    url = "https://gnews.io/api/v4/search"
    params = {"q": query, "lang": lang, "max": max_results, "token": token}
    to = float(os.environ.get("HTTP_TIMEOUT_SECONDS", "20"))
    
    try:
        r = requests.get(url, params=params, timeout=to)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[GNews] Fetch failed: {e}")
        return []
    
    articles = data.get("articles", [])
    items = []
    
    for article in articles:
        # Extract and normalize fields
        title = (article.get("title") or "").strip()
        content = (article.get("content") or article.get("description") or "").strip()
        link = (article.get("url") or "").strip()
        source_name = (article.get("source", {}).get("name") or "GNews").strip()
        published = article.get("publishedAt", "")
        
        # Skip items without essential data
        if not title and not content:
            continue
        
        # Generate deterministic ID
        item_id = article.get("id") or link or str(uuid.uuid4())
        
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
            "_ingestion_method": "gnews_api",
            "_query": query,
            "_language": lang
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