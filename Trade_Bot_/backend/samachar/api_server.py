"""
Samachar API Server - FastAPI endpoint for Samruddhi integration
Exposes contract-compliant news items via REST API.

CRITICAL RULES:
- Only return validated contract objects
- No partial garbage
- No UI-specific data
- Failure-safe: empty feed returns {"count": 0, "items": []}
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.samachar_pipeline import SamacharPipeline
from contract_validator import validate_contract_item, ContractValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("samachar_api")

app = FastAPI(
    title="Samachar News Ingestion API",
    description="Deterministic news ingestion engine outputting contract-compliant signals for Samruddhi",
    version="1.0.0"
)

# CORS for Samruddhi backend (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache (replace with Redis/DB in production)
_latest_items: List[Dict[str, Any]] = []
_last_updated: Optional[str] = None
_pipeline_errors: List[str] = []


@app.on_event("startup")
async def startup_event():
    """Initialize pipeline and cache on startup."""
    global _latest_items, _last_updated, _pipeline_errors
    logger.info("[SamacharAPI] Starting up...")
    
    _pipeline_errors = []
    
    # Optional: Pre-warm cache
    if os.environ.get("SAMACHAR_PREWARM", "false").lower() == "true":
        logger.info("[SamacharAPI] Pre-warming cache...")
        try:
            _refresh_cache()
        except Exception as e:
            logger.error(f"[SamacharAPI] Pre-warm failed: {e}")
            _pipeline_errors.append(f"Startup pre-warm failed: {str(e)}")


def _refresh_cache():
    """
    Refresh cached news items with comprehensive failure handling.
    
    FAILURE HANDLING:
    - Empty feed: Returns {"count": 0, "items": []}
    - Partial failure: Skips bad items, continues processing
    - Source failure: Continues with other sources
    - Invalid data: Drops before contract stage
    """
    global _latest_items, _last_updated, _pipeline_errors
    
    logger.info("[SamacharAPI] Refreshing cache...")
    _pipeline_errors = []  # Clear previous errors
    
    try:
        config = _load_config()
        pipeline = SamacharPipeline(config)
        
        # Run pipeline with error isolation
        items = []
        try:
            items = pipeline.run_full_pipeline()
        except Exception as e:
            error_msg = f"Pipeline execution failed: {str(e)}"
            logger.error(f"[SamacharAPI] {error_msg}")
            _pipeline_errors.append(error_msg)
            items = []  # Fallback to empty
        
        # Validate each item individually (drop invalid ones)
        validated_items = []
        for i, item in enumerate(items):
            try:
                validate_contract_item(item)
                validated_items.append(item)
            except ContractValidationError as e:
                warning_msg = f"Item {i} failed validation, dropping: {str(e)}"
                logger.warning(f"[SamacharAPI] {warning_msg}")
                _pipeline_errors.append(warning_msg)
                continue
        
        _latest_items = validated_items
        _last_updated = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"[SamacharAPI] Cache refreshed: {len(_latest_items)} validated items")
        
    except Exception as e:
        error_msg = f"Cache refresh critical failure: {str(e)}"
        logger.error(f"[SamacharAPI] {error_msg}")
        _pipeline_errors.append(error_msg)
        _latest_items = []  # Safe fallback


def _load_config():
    """Load pipeline configuration."""
    default_config = {
        "rss_feeds": [
            "https://news.google.com/rss?topic=business&hl=en-IN&gl=IN&ceid=IN:en",
            "https://economictimes.indiatimes.com/rssfeeddefault.cms"
        ],
        "queries": ["Indian stock market", "NSE BSE news", "RBI policy"],
        "max_results_per_source": int(os.environ.get("SAMACHAR_MAX_RESULTS", "10"))
    }
    
    if os.environ.get("SAMACHAR_CONFIG"):
        try:
            default_config.update(json.loads(os.environ["SAMACHAR_CONFIG"]))
        except Exception as e:
            print(f"[SamacharAPI] Config parse error: {e}")
    
    return default_config


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if _latest_items else "degraded",
        "service": "samachar-ingestion",
        "version": "1.0.0",
        "last_updated": _last_updated,
        "cached_items": len(_latest_items),
        "errors": _pipeline_errors[-5:] if _pipeline_errors else []  # Last 5 errors
    }


@app.get("/api/v1/samachar/feed")
async def get_samachar_feed(
    limit: int = Query(50, ge=1, le=200, description="Max items to return"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (positive/negative/neutral)"),
    min_impact: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum impact score"),
    force_refresh: bool = Query(False, description="Force pipeline refresh")
):
    """
    PRIMARY ENDPOINT: Get contract-compliant news feed for Samruddhi.
    
    Returns only validated contract objects conforming to samachar_contract_v1.json.
    
    FAILURE HANDLING:
    - Empty feed: {"count": 0, "items": []}
    - Partial failure: Bad items already filtered during refresh
    - Source failure: Other sources continue normally
    - Invalid data: Dropped before reaching this endpoint
    """
    global _latest_items, _last_updated
    
    # Refresh if requested or cache is empty/stale
    if force_refresh or not _latest_items:
        try:
            _refresh_cache()
        except Exception as e:
            logger.error(f"[SamacharAPI] Refresh failed: {e}")
            # Return empty feed instead of error (failure-safe)
            return {
                "count": 0,
                "items": [],
                "contract_version": "v1.0",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "warnings": [f"Refresh failed: {str(e)}"]
            }
    
    # Filter items
    filtered = _latest_items
    
    if sector:
        filtered = [
            item for item in filtered
            if item.get("market_relevance", {}).get("sector") == sector
        ]
    
    if sentiment:
        filtered = [
            item for item in filtered
            if item.get("sentiment", {}).get("label") == sentiment
        ]
    
    if min_impact is not None:
        filtered = [
            item for item in filtered
            if item.get("market_relevance", {}).get("impact_score", 0) >= min_impact
        ]
    
    # Apply limit
    filtered = filtered[:limit]
    
    # Return contract-compliant response
    return {
        "count": len(filtered),
        "items": filtered,
        "contract_version": "v1.0",
        "generated_at": _last_updated,
        "filters_applied": {
            "sector": sector,
            "sentiment": sentiment,
            "min_impact": min_impact,
            "limit": limit
        }
    }


@app.get("/api/v1/news")
async def get_news(
    limit: int = Query(50, ge=1, le=200, description="Max items to return"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (positive/negative/neutral)"),
    min_impact: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum impact score"),
    force_refresh: bool = Query(False, description="Force pipeline refresh")
):
    """
    DEPRECATED: Use /api/v1/samachar/feed instead.
    Legacy endpoint for backward compatibility.
    """
    logger.warning("[SamacharAPI] Deprecated endpoint /api/v1/news called, use /api/v1/samachar/feed")
    return await get_samachar_feed(limit, sector, sentiment, min_impact, force_refresh)


@app.get("/api/v1/news/latest")
async def get_latest_news():
    """Get the single most recent news item."""
    if not _latest_items:
        return {"count": 0, "item": None}
    
    return {
        "count": 1,
        "item": _latest_items[0]
    }


@app.get("/api/v1/news/{item_id}")
async def get_news_by_id(item_id: str):
    """Get a specific news item by ID."""
    for item in _latest_items:
        if item.get("id") == item_id:
            return {
                "count": 1,
                "item": item
            }
    
    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")


@app.post("/api/v1/refresh")
async def refresh_news():
    """Manually trigger pipeline refresh."""
    try:
        _refresh_cache()
        return {
            "status": "success",
            "message": f"Pipeline refreshed. {len(_latest_items)} items cached.",
            "last_updated": _last_updated,
            "count": len(_latest_items)
        }
    except Exception as e:
        logger.error(f"[SamacharAPI] Manual refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@app.get("/api/v1/sectors")
async def get_available_sectors():
    """Get list of available sectors in cached news."""
    if not _latest_items:
        return {"sectors": []}
    
    sectors = set()
    for item in _latest_items:
        sector = item.get("market_relevance", {}).get("sector")
        if sector:
            sectors.add(sector)
    
    return {
        "sectors": sorted(list(sectors)),
        "total_items": len(_latest_items)
    }


@app.get("/api/v1/stats")
async def get_stats():
    """Get statistics about cached news."""
    if not _latest_items:
        return {"message": "No news items cached"}
    
    # Sentiment distribution
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    for item in _latest_items:
        label = item.get("sentiment", {}).get("label", "neutral")
        sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
    
    # Sector distribution
    sector_counts = {}
    for item in _latest_items:
        sector = item.get("market_relevance", {}).get("sector", "general")
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
    
    # Impact score stats
    impact_scores = [
        item.get("market_relevance", {}).get("impact_score", 0)
        for item in _latest_items
    ]
    avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0
    
    return {
        "total_items": len(_latest_items),
        "last_updated": _last_updated,
        "sentiment_distribution": sentiment_counts,
        "sector_distribution": sector_counts,
        "average_impact_score": round(avg_impact, 2),
        "contract_version": "v1.0"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("SAMACHAR_API_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
