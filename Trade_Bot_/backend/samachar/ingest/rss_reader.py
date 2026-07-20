import time
import uuid
import feedparser
from datetime import datetime, timezone

def fetch_rss(url, limit=20):
    """
    Fetch RSS feed and return structured, contract-ready raw items.
    All items include mandatory source tagging and normalized fields.
    """
    feed = feedparser.parse(url)
    items = []
    
    # Extract source metadata
    feed_title = feed.get("feed", {}).get("title", "")
    feed_link = feed.get("feed", {}).get("link", url)
    source_name = feed_title if feed_title else url
    
    for entry in feed.get("entries", [])[:limit]:
        # Extract and normalize fields
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = entry.get("summary", "").strip()
        published = entry.get("published", "")
        
        # Skip items without essential data
        if not title and not summary:
            continue
        
        # Generate deterministic ID
        item_id = entry.get("id") or link or str(uuid.uuid4())
        
        # Normalize timestamp to ISO 8601
        timestamp = _normalize_timestamp(published)
        
        items.append({
            "id": item_id,
            "timestamp": timestamp,
            "source": source_name,
            "source_url": url,
            "title": title,
            "content": summary,  # RSS summary becomes initial content
            "link": link,
            "published": published,
            "_ingestion_method": "rss",
            "_raw_feed_title": feed_title
        })
    
    return items

def _normalize_timestamp(published_str):
    """Convert RSS timestamp to ISO 8601 UTC format."""
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