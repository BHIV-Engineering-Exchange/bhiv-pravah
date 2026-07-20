"""
Market intelligence enrichment for Samruddhi predictions.

This module converts model outputs and cached technical features into
decision-support context: market behavior, evolving patterns, momentum shifts,
breakout quality, exhaustion, risk, and plain-language guidance.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


FEATURE_DIR = Path(__file__).resolve().parent / "data" / "features"


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_features(symbol: str) -> Dict[str, Any]:
    feature_path = FEATURE_DIR / f"{symbol}_features.json"
    if not feature_path.exists():
        return {}
    try:
        with feature_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload.get("current_features", {}) or {}
    except Exception:
        return {}


def _label_market_context(features: Dict[str, Any], prediction: Dict[str, Any]) -> Dict[str, Any]:
    volatility = _as_float(features.get("volatility_20"))
    atr = _as_float(features.get("ATR"))
    price = _as_float(prediction.get("current_price") or features.get("Close"))
    bb_width = _as_float(features.get("BB_width"))
    adx = _as_float(features.get("ADX"))
    trend = _as_float(features.get("trend_direction"))
    market_state = (
        prediction.get("price_metadata", {}).get("market_state")
        or prediction.get("data_status", {}).get("market_context")
        or "NORMAL"
    )

    if str(market_state).upper() in {"CLOSED", "MARKET_CLOSED"}:
        context = "MARKET_CLOSED"
    elif str(market_state).upper() in {"PRE", "POST", "EVENT_WINDOW"}:
        context = "EVENT_WINDOW"
    elif volatility > 0.35 or (price > 0 and atr / price > 0.035) or bb_width > 9:
        context = "HIGH_VOLATILITY"
    else:
        context = "NORMAL"

    if adx >= 25 and trend > 0:
        regime = "TRENDING_UP"
    elif adx >= 25 and trend < 0:
        regime = "TRENDING_DOWN"
    elif volatility > 0.35:
        regime = "VOLATILE"
    else:
        regime = "RANGING"

    return {
        "market_context": context,
        "regime": regime,
        "volatility": round(volatility, 4),
        "atr_percent": round((atr / price) * 100, 2) if price > 0 else None,
        "trend_strength": "strong" if adx >= 25 else "moderate" if adx >= 18 else "weak",
        "adx": round(adx, 2),
    }


def _detect_patterns(features: Dict[str, Any], prediction: Dict[str, Any]) -> Dict[str, Any]:
    price = _as_float(prediction.get("current_price") or features.get("Close"))
    action = str(prediction.get("action", "HOLD")).upper()
    predicted_return = _as_float(prediction.get("predicted_return"))
    confidence = _as_float(prediction.get("confidence"))

    rsi = _as_float(features.get("RSI_14"), 50)
    macd_hist = _as_float(features.get("MACD_hist"))
    macd_increasing = _as_float(features.get("macd_hist_increasing"))
    bb_pct = _as_float(features.get("BB_pct", features.get("bb_position")), 0.5)
    volume_ratio = _as_float(features.get("volume_ratio"), 1.0)
    higher_high = _as_float(features.get("higher_high"))
    lower_low = _as_float(features.get("lower_low"))
    price_to_sma10 = _as_float(features.get("price_to_sma_10"), 1.0)
    price_to_sma50 = _as_float(features.get("price_to_sma_50"), 1.0)

    momentum_shift = "neutral"
    if macd_hist > 0 and macd_increasing > 0 and rsi >= 52:
        momentum_shift = "bullish_improving"
    elif macd_hist < 0 and macd_increasing <= 0 and rsi <= 48:
        momentum_shift = "bearish_worsening"
    elif macd_increasing > 0:
        momentum_shift = "improving"
    elif macd_increasing <= 0:
        momentum_shift = "fading"

    breakout_state = "none"
    breakout_quality = "not_applicable"
    if bb_pct >= 0.95 or higher_high > 0:
        breakout_state = "upside_breakout_attempt"
        breakout_quality = "validated" if volume_ratio >= 1.1 and predicted_return > 0 and confidence >= 0.6 else "low_probability"
    elif bb_pct <= 0.05 or lower_low > 0:
        breakout_state = "downside_breakout_attempt"
        breakout_quality = "validated" if volume_ratio >= 1.1 and predicted_return < 0 and confidence >= 0.6 else "low_probability"

    exhaustion = "none"
    if rsi >= 70 or (bb_pct > 1.0 and volume_ratio < 0.8):
        exhaustion = "upside_exhaustion_risk"
    elif rsi <= 30 or (bb_pct < 0.0 and volume_ratio < 0.8):
        exhaustion = "downside_exhaustion_risk"

    continuation = "unclear"
    if action == "LONG" and price_to_sma10 > 1 and price_to_sma50 > 1 and momentum_shift in {"bullish_improving", "improving"}:
        continuation = "bullish_continuation"
    elif action == "SHORT" and price_to_sma10 < 1 and price_to_sma50 < 1 and momentum_shift in {"bearish_worsening", "fading"}:
        continuation = "bearish_continuation"
    elif action in {"LONG", "SHORT"}:
        continuation = "needs_confirmation"

    return {
        "momentum_shift": momentum_shift,
        "breakout_state": breakout_state,
        "breakout_quality": breakout_quality,
        "continuation_vs_exhaustion": continuation,
        "exhaustion_risk": exhaustion,
        "evolving_patterns": [
            item
            for item in [momentum_shift, breakout_state, continuation, exhaustion]
            if item not in {"neutral", "none", "unclear"}
        ],
    }


def _build_decision_support(
    features: Dict[str, Any],
    prediction: Dict[str, Any],
    context: Dict[str, Any],
    patterns: Dict[str, Any],
) -> Dict[str, Any]:
    action = str(prediction.get("action", "HOLD")).upper()
    confidence = _as_float(prediction.get("confidence"))
    predicted_return = _as_float(prediction.get("predicted_return"))
    warnings = prediction.get("warnings") or []
    high_disagreement = bool(prediction.get("prediction_analysis", {}).get("high_disagreement"))

    strength = []
    weakness = []
    risk = []

    if action == "LONG" and predicted_return > 0:
        strength.append("price models lean upward")
    if action == "SHORT" and predicted_return < 0:
        weakness.append("price models lean downward")
    if patterns["momentum_shift"] in {"bullish_improving", "improving"}:
        strength.append("momentum is improving")
    if patterns["momentum_shift"] in {"bearish_worsening", "fading"}:
        weakness.append("momentum is fading")
    if patterns["breakout_quality"] == "validated":
        strength.append("breakout has volume/model confirmation")
    if patterns["breakout_quality"] == "low_probability":
        risk.append("breakout attempt lacks confirmation")
    if patterns["exhaustion_risk"] != "none":
        risk.append(patterns["exhaustion_risk"].replace("_", " "))
    if high_disagreement or confidence < 0.6:
        risk.append("model agreement is not strong")
    if context["market_context"] in {"HIGH_VOLATILITY", "EVENT_WINDOW", "MARKET_CLOSED"}:
        risk.append(f"market context is {context['market_context'].lower()}")
    if warnings:
        risk.extend(str(w) for w in warnings[:2])

    if action in {"LONG", "SHORT"} and confidence >= 0.7 and not risk:
        decision = "clearer_trade_filter"
    elif action in {"LONG", "SHORT"} and confidence >= 0.5:
        decision = "confirmation_required"
    else:
        decision = "wait_for_clarity"

    return {
        "directional_bias": "bullish" if action == "LONG" else "bearish" if action == "SHORT" else "neutral",
        "decision_support": decision,
        "not_a_sell_signal": True,
        "strength_building": strength,
        "weakness_forming": weakness,
        "risk_increasing": risk,
        "low_probability_trade_filter": len(risk) > 0 or confidence < 0.6,
        "confirmation_layer": {
            "confidence": round(confidence, 4),
            "models_align": bool(prediction.get("ensemble_details", {}).get("models_align")),
            "price_agreement": bool(prediction.get("ensemble_details", {}).get("price_agreement")),
        },
        "plain_language_summary": _summary(action, predicted_return, confidence, context, patterns, risk),
    }


def _summary(
    action: str,
    predicted_return: float,
    confidence: float,
    context: Dict[str, Any],
    patterns: Dict[str, Any],
    risk: List[str],
) -> str:
    bias = "bullish" if action == "LONG" else "bearish" if action == "SHORT" else "neutral"
    if action == "HOLD":
        return "No clear directional edge yet; wait for stronger alignment."
    caution = " Risk is elevated; use this as confirmation, not as an entry command." if risk else ""
    return (
        f"{bias.capitalize()} bias with {confidence:.0%} confidence and expected move "
        f"{predicted_return:+.2f}%. Context is {context['regime'].lower()}; "
        f"pattern read is {patterns['continuation_vs_exhaustion'].replace('_', ' ')}."
        f"{caution}"
    )


def enrich_prediction(prediction: Dict[str, Any]) -> Dict[str, Any]:
    """Return prediction enriched with Samruddhi market-intelligence fields."""
    if not prediction or prediction.get("error") or not prediction.get("symbol"):
        return prediction

    symbol = str(prediction["symbol"])
    features = prediction.get("feature_snapshot") or _load_features(symbol)
    context = _label_market_context(features, prediction)
    patterns = _detect_patterns(features, prediction)
    support = _build_decision_support(features, prediction, context, patterns)

    enriched = prediction.copy()
    enriched["market_intelligence"] = {
        "generated_at": datetime.now().isoformat(),
        "price_behavior": {
            "current_price": prediction.get("current_price"),
            "predicted_return": prediction.get("predicted_return"),
            "action": prediction.get("action"),
        },
        "market_context": context,
        "evolving_patterns": patterns,
        **support,
    }

    data_status = dict(enriched.get("data_status") or {})
    if context.get("market_context"):
        data_status["market_context"] = context["market_context"]
    if data_status:
        enriched["data_status"] = data_status

    return enriched


def enrich_predictions_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich every prediction in a standard response payload."""
    if not isinstance(response, dict):
        return response
    enriched = response.copy()
    if isinstance(enriched.get("predictions"), list):
        enriched["predictions"] = [enrich_prediction(item) for item in enriched["predictions"]]
    return enriched
