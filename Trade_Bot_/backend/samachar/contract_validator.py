"""
Samachar Output Contract Validator & Formatter
Ensures all news items conform to samachar_contract_v1.json before delivery to Samruddhi.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


# Sector mapping for market relevance
SECTOR_KEYWORDS = {
    "technology": ["tech", "software", "AI", "artificial intelligence", "startup", "digital", "IT", "cyber"],
    "banking": ["bank", "RBI", "interest rate", "loan", "credit", "financial", "NPA", "deposit"],
    "pharma": ["pharma", "drug", "medicine", "vaccine", "clinical", "FDA", "biotech", "healthcare"],
    "energy": ["oil", "gas", "energy", "petroleum", "ONGC", "reliance", "power", "coal", "renewable"],
    "auto": ["auto", "vehicle", "car", "Tata Motors", "Maruti", "Mahindra", "EV", "electric vehicle"],
    "FMCG": ["FMCG", "consumer", "HUL", "ITC", "Nestle", "FMCG", "retail", "goods"],
    "metals": ["metal", "steel", "aluminum", "Tata Steel", "Hindalco", "mining", "iron"],
    "real_estate": ["real estate", "property", "housing", "infrastructure", "construction"],
    "telecom": ["telecom", "Jio", "Airtel", "Vi", "5G", "tower", "spectrum"],
    "finance": ["finance", "stock", "market", "Sensex", "Nifty", "IPO", "mutual fund", "investment"],
    "agriculture": ["agriculture", "farm", "crop", "monsoon", "MSP", "fertilizer"],
}


class ContractValidationError(Exception):
    """Raised when a news item fails contract validation."""
    pass


def validate_contract_item(item: Dict[str, Any]) -> bool:
    """
    Validate a news item against the Samachar v1 contract.
    Returns True if valid, raises ContractValidationError if invalid.
    """
    errors = []
    
    # Required fields check
    required_fields = ["id", "timestamp", "source", "title", "content", "summary", "sentiment", "market_relevance", "ingestion_ready"]
    for field in required_fields:
        if field not in item:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        raise ContractValidationError(f"Contract validation failed: {', '.join(errors)}")
    
    # Type and format validation
    if not isinstance(item.get("id"), str) or len(item["id"]) == 0:
        errors.append("Field 'id' must be a non-empty string")
    
    if not isinstance(item.get("timestamp"), str) or len(item["timestamp"]) == 0:
        errors.append("Field 'timestamp' must be a non-empty ISO 8601 string")
    
    if not isinstance(item.get("source"), str) or len(item["source"]) == 0:
        errors.append("Field 'source' must be a non-empty string")
    
    if not isinstance(item.get("title"), str) or len(item["title"]) == 0:
        errors.append("Field 'title' must be a non-empty string")
    
    if not isinstance(item.get("content"), str) or len(item["content"]) < 10:
        errors.append("Field 'content' must be a string with at least 10 characters")
    
    # Summary validation
    summary = item.get("summary", {})
    if not isinstance(summary, dict):
        errors.append("Field 'summary' must be an object")
    else:
        if "text" not in summary or not isinstance(summary["text"], str):
            errors.append("Field 'summary.text' must be a string")
        if "confidence" not in summary or not isinstance(summary["confidence"], (int, float)):
            errors.append("Field 'summary.confidence' must be a float")
        elif not (0.0 <= summary["confidence"] <= 1.0):
            errors.append("Field 'summary.confidence' must be between 0.0 and 1.0")
    
    # Sentiment validation
    sentiment = item.get("sentiment", {})
    if not isinstance(sentiment, dict):
        errors.append("Field 'sentiment' must be an object")
    else:
        if sentiment.get("label") not in ["positive", "negative", "neutral"]:
            errors.append("Field 'sentiment.label' must be 'positive', 'negative', or 'neutral'")
        if "score" not in sentiment or not isinstance(sentiment["score"], (int, float)):
            errors.append("Field 'sentiment.score' must be a float")
        elif not (-1.0 <= sentiment["score"] <= 1.0):
            errors.append("Field 'sentiment.score' must be between -1.0 and 1.0")
    
    # Market relevance validation
    market_relevance = item.get("market_relevance", {})
    if not isinstance(market_relevance, dict):
        errors.append("Field 'market_relevance' must be an object")
    else:
        if "impact_score" not in market_relevance or not isinstance(market_relevance["impact_score"], (int, float)):
            errors.append("Field 'market_relevance.impact_score' must be a float")
        elif not (0.0 <= market_relevance["impact_score"] <= 1.0):
            errors.append("Field 'market_relevance.impact_score' must be between 0.0 and 1.0")
    
    # ingestion_ready must be True
    if item.get("ingestion_ready") is not True:
        errors.append("Field 'ingestion_ready' must be True")
    
    if errors:
        raise ContractValidationError(f"Contract validation failed: {'; '.join(errors)}")
    
    return True


def format_to_contract(
    raw_item: Dict[str, Any],
    summary_result: Dict[str, Any],
    sentiment_result: Dict[str, Any],
    sector: Optional[str] = None,
    impact_score: Optional[float] = None,
    entities: Optional[List[str]] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Transform raw processed news item into contract-compliant format.
    
    Args:
        raw_item: Raw news item from ingestion layer
        summary_result: Output from summarizer.summarize_*()
        sentiment_result: Output from sentiment.analyze()
        sector: Market sector (auto-detected if None)
        impact_score: Market impact score (auto-calculated if None)
        entities: Named entities (optional)
        tags: Categorization tags (optional)
    
    Returns:
        Contract-compliant news item ready for Samruddhi
    """
    # Auto-detect sector if not provided
    if sector is None:
        sector = _detect_sector(raw_item.get("title", "") + " " + raw_item.get("content", ""))
    
    # Auto-calculate impact score if not provided
    if impact_score is None:
        impact_score = _calculate_impact_score(raw_item, sentiment_result)
    
    # Build contract item
    contract_item = {
        "id": raw_item.get("id", str(uuid.uuid4())),
        "timestamp": raw_item.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "source": raw_item.get("source", "unknown"),
        "title": (raw_item.get("title") or "").strip(),
        "content": (raw_item.get("content") or "").strip(),
        "summary": {
            "text": summary_result.get("text", ""),
            "confidence": summary_result.get("confidence", 0.5)
        },
        "sentiment": {
            "label": sentiment_result.get("label", "neutral"),
            "score": sentiment_result.get("score", 0.0)
        },
        "entities": entities or [],
        "tags": tags or [],
        "market_relevance": {
            "sector": sector,
            "impact_score": round(impact_score, 2)
        },
        "ingestion_ready": True
    }
    
    # Validate before returning
    validate_contract_item(contract_item)
    
    return contract_item


def _detect_sector(text: str) -> Optional[str]:
    """Detect market sector from text using keyword matching."""
    text_lower = text.lower()
    
    sector_scores = {}
    for sector, keywords in SECTOR_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            sector_scores[sector] = score
    
    if sector_scores:
        return max(sector_scores.items(), key=lambda x: x[1])[0]
    
    return "general"


def _calculate_impact_score(raw_item: Dict[str, Any], sentiment_result: Dict[str, Any]) -> float:
    """
    Calculate market impact score based on:
    - Sentiment strength
    - Content length (proxy for significance)
    - Urgency indicators
    """
    score = 0.3  # Base score
    
    # Sentiment strength contribution (0.0 - 0.4)
    sentiment_score = abs(sentiment_result.get("score", 0.0))
    score += sentiment_score * 0.4
    
    # Content significance (0.0 - 0.2)
    content_length = len(raw_item.get("content", ""))
    if content_length > 500:
        score += 0.2
    elif content_length > 200:
        score += 0.1
    
    # Urgency boost (0.0 - 0.1)
    tone = sentiment_result.get("tone", "calm")
    if tone == "urgent":
        score += 0.1
    
    return min(1.0, score)


def batch_format_to_contract(
    raw_items: List[Dict[str, Any]],
    summaries: List[Dict[str, Any]],
    sentiments: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Batch format multiple news items to contract format.
    
    Args:
        raw_items: List of raw news items
        summaries: List of summary results (same order as raw_items)
        sentiments: List of sentiment results (same order as raw_items)
    
    Returns:
        List of contract-compliant news items
    """
    if len(raw_items) != len(summaries) or len(raw_items) != len(sentiments):
        raise ValueError("raw_items, summaries, and sentiments must have the same length")
    
    contract_items = []
    for raw, summary, sentiment in zip(raw_items, summaries, sentiments):
        try:
            item = format_to_contract(raw, summary, sentiment)
            contract_items.append(item)
        except ContractValidationError as e:
            print(f"[ContractValidator] Skipping invalid item: {e}")
            continue
    
    return contract_items
