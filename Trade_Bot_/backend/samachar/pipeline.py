"""
Samachar Pipeline Executor - Contract-Compliant Output
Transforms raw news through ingestion → processing → contract validation → Samruddhi-ready output.

FAILURE HANDLING:
- Empty feed: Returns []
- Partial failure: Skips bad items, continues processing
- Source failure: Continues with other sources
- Invalid data: Drops before contract stage
"""

import os
import sys
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("samachar_pipeline")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.rss_reader import fetch_rss
from ingest.gnews import fetch_gnews
from ingest.newsdata import fetch_newsdata
from ingest.cleaner import clean_article
from agents.summarizer import summarize_short, summarize_medium
from agents.sentiment import analyze as analyze_sentiment
from contract_validator import format_to_contract, batch_format_to_contract, validate_contract_item


class SamacharPipeline:
    """
    Deterministic news ingestion pipeline that outputs contract-compliant items for Samruddhi.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.sources = self.config.get("sources", [])
        self.queries = self.config.get("queries", ["market news", "stock market"])
        self.max_results_per_source = self.config.get("max_results_per_source", 10)
    
    def run_full_pipeline(self) -> List[Dict[str, Any]]:
        """
        Execute complete pipeline: Ingest → Clean → Process → Validate → Contract Output
        
        FAILURE HANDLING:
        - Any stage failure returns partial results instead of crashing
        - Invalid items are dropped, valid ones continue
        """
        logger.info("[Pipeline] Starting full pipeline execution...")
        
        try:
            # Step 1: Ingest from all sources
            raw_items = self._ingest_all_sources()
            logger.info(f"[Pipeline] Ingested {len(raw_items)} raw items")
            
            if not raw_items:
                logger.warning("[Pipeline] No items ingested. Returning empty.")
                return []
            
            # Step 2: Clean and deduplicate
            cleaned_items = self._clean_and_deduplicate(raw_items)
            logger.info(f"[Pipeline] Cleaned and deduplicated to {len(cleaned_items)} items")
            
            if not cleaned_items:
                logger.warning("[Pipeline] No items after cleaning. Returning empty.")
                return []
            
            # Step 3: Process (summarize + sentiment)
            processed_items = self._process_items(cleaned_items)
            logger.info(f"[Pipeline] Processed {len(processed_items)} items")
            
            if not processed_items:
                logger.warning("[Pipeline] No items after processing. Returning empty.")
                return []
            
            # Step 4: Format to contract
            contract_items = self._format_to_contract(processed_items)
            logger.info(f"[Pipeline] Formatted {len(contract_items)} items to contract")
            
            # Step 5: Validate (already done in formatting, double-check)
            valid_items = []
            for i, item in enumerate(contract_items):
                try:
                    validate_contract_item(item)
                    valid_items.append(item)
                except Exception as e:
                    logger.warning(f"[Pipeline] Item {i} failed final validation, dropping: {e}")
                    continue
            
            logger.info(f"[Pipeline] Validation passed for {len(valid_items)} items")
            return valid_items
            
        except Exception as e:
            logger.error(f"[Pipeline] Critical failure: {e}")
            return []  # Safe fallback
    
    def _ingest_all_sources(self) -> List[Dict[str, Any]]:
        """
        Fetch news from all configured sources.
        
        FAILURE HANDLING:
        - Individual source failures don't break the pipeline
        - Continues with remaining sources if one fails
        """
        all_items = []
        
        # RSS feeds
        rss_feeds = self.config.get("rss_feeds", [])
        for feed_url in rss_feeds:
            try:
                logger.info(f"[Ingestion] Fetching RSS: {feed_url}")
                items = fetch_rss(feed_url, limit=self.max_results_per_source)
                all_items.extend(items)
                logger.info(f"[Ingestion] RSS success: {len(items)} items from {feed_url}")
            except Exception as e:
                logger.warning(f"[Ingestion] RSS fetch failed for {feed_url}: {e}")
                continue  # Continue with next source
        
        # GNews API
        if os.environ.get("GNEWS_API_KEY"):
            for query in self.queries:
                try:
                    logger.info(f"[Ingestion] Fetching GNews: {query}")
                    items = fetch_gnews(query, max_results=self.max_results_per_source)
                    all_items.extend(items)
                    logger.info(f"[Ingestion] GNews success: {len(items)} items for '{query}'")
                except Exception as e:
                    logger.warning(f"[Ingestion] GNews fetch failed for '{query}': {e}")
                    continue  # Continue with next query
        else:
            logger.info("[Ingestion] GNews API key not configured, skipping")
        
        # NewsData API
        if os.environ.get("NEWSDATA_API_KEY"):
            for query in self.queries:
                try:
                    logger.info(f"[Ingestion] Fetching NewsData: {query}")
                    items = fetch_newsdata(query, page_size=self.max_results_per_source)
                    all_items.extend(items)
                    logger.info(f"[Ingestion] NewsData success: {len(items)} items for '{query}'")
                except Exception as e:
                    logger.warning(f"[Ingestion] NewsData fetch failed for '{query}': {e}")
                    continue  # Continue with next query
        else:
            logger.info("[Ingestion] NewsData API key not configured, skipping")
        
        logger.info(f"[Ingestion] Total items from all sources: {len(all_items)}")
        return all_items
    
    def _clean_and_deduplicate(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean articles and remove duplicates based on title similarity."""
        cleaned = []
        seen_titles = set()
        
        for item in items:
            try:
                # Clean article
                article = clean_article(item)
                
                # Deduplicate by title (case-insensitive)
                title_key = article.get("title", "").lower().strip()
                if not title_key or title_key in seen_titles:
                    continue
                
                seen_titles.add(title_key)
                cleaned.append(article)
            except Exception as e:
                print(f"[Cleaner] Failed to clean item: {e}")
                continue
        
        return cleaned
    
    def _process_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run summarization and sentiment analysis on all items."""
        processed = []
        
        for item in items:
            try:
                content = item.get("content", "") + " " + item.get("title", "")
                
                # Summarize
                summary = summarize_short(content)
                
                # Sentiment analysis
                sentiment = analyze_sentiment(content)
                
                # Attach to item
                item["_summary"] = summary
                item["_sentiment"] = sentiment
                
                processed.append(item)
            except Exception as e:
                print(f"[Processor] Failed to process item: {e}")
                continue
        
        return processed
    
    def _format_to_contract(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform processed items into contract-compliant format."""
        contract_items = []
        
        for item in items:
            try:
                summary = item.pop("_summary", {"text": "", "confidence": 0.5})
                sentiment = item.pop("_sentiment", {"label": "neutral", "score": 0.0})
                
                # Format to contract
                contract_item = format_to_contract(
                    raw_item=item,
                    summary_result=summary,
                    sentiment_result=sentiment
                )
                
                contract_items.append(contract_item)
            except Exception as e:
                print(f"[Formatter] Failed to format item: {e}")
                continue
        
        return contract_items
    
    def _validate_all(self, items: List[Dict[str, Any]]):
        """Validate all items against contract."""
        for i, item in enumerate(items):
            try:
                validate_contract_item(item)
            except Exception as e:
                print(f"[Validator] Item {i} failed validation: {e}")
                raise
    
    def export_to_file(self, items: List[Dict[str, Any]], output_path: str):
        """Export contract-compliant items to JSON file."""
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_items": len(items),
                "contract_version": "v1.0",
                "items": items
            }, f, ensure_ascii=False, indent=2)
        
        print(f"[Export] Saved {len(items)} items to {output_path}")


def run_pipeline_standalone():
    """Run pipeline as standalone script (for testing/cron)."""
    # Default configuration
    config = {
        "rss_feeds": [
            "https://news.google.com/rss?topic=business&hl=en-IN&gl=IN&ceid=IN:en",
            "https://economictimes.indiatimes.com/rssfeeddefault.cms"
        ],
        "queries": ["Indian stock market", "NSE BSE news", "RBI policy"],
        "max_results_per_source": 10
    }
    
    # Load from environment if available
    if os.environ.get("SAMACHAR_CONFIG"):
        try:
            config = json.loads(os.environ["SAMACHAR_CONFIG"])
        except Exception as e:
            print(f"[Config] Failed to parse SAMACHAR_CONFIG: {e}")
    
    # Run pipeline
    pipeline = SamacharPipeline(config)
    items = pipeline.run_full_pipeline()
    
    # Export
    if items:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "contract_output")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"samachar_output_{timestamp}.json")
        pipeline.export_to_file(items, output_path)
        
        # Also save as latest for Samruddhi to consume
        latest_path = os.path.join(output_dir, "latest.json")
        pipeline.export_to_file(items, latest_path)
        
        print(f"\n[Pipeline] Complete! {len(items)} contract-compliant items ready for Samruddhi.")
    else:
        print("\n[Pipeline] No items generated.")


if __name__ == "__main__":
    run_pipeline_standalone()
