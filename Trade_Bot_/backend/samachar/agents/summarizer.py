import os
import re
import requests


def _sentences(text):
    """Split text into sentences deterministically."""
    t = text or ""
    s = re.split(r"(?<=[\.!?])\s+", t)
    return [x.strip() for x in s if x.strip()]


def _fallback_short(text):
    """Generate short summary (2 sentences, max 400 chars)."""
    s = _sentences(text)
    return " ".join(s[:2])[:400]


def _fallback_medium(text):
    """Generate medium summary (4 sentences, max 800 chars)."""
    s = _sentences(text)
    return " ".join(s[:4])[:800]


def _uniguru(text):
    """Call UniGuru summarization API (optional external service)."""
    url = os.environ.get("UNIGRUGU_BASE_URL")  # Fixed env var name
    key = os.environ.get("UNIGURU_API_KEY")  # Fixed env var name
    if not url:
        return None
    try:
        to = float(os.environ.get("HTTP_TIMEOUT_SECONDS", "20"))
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        payload = {"text": text}
        r = requests.post(url, json=payload, headers=headers, timeout=to)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def summarize_short(text):
    """
    Generate short summary with confidence score.
    Returns: {"text": str, "confidence": float}
    """
    if not text or len(text.strip()) < 10:
        return {"text": "", "confidence": 0.0}

    res = _uniguru(text)
    if isinstance(res, dict) and res.get("summary_short"):
        summary_text = res.get("summary_short")
        confidence = 0.85  # High confidence for AI-generated
        return {"text": summary_text, "confidence": confidence}

    # Fallback to heuristic
    summary_text = _fallback_short(text)
    # Confidence based on text quality
    sentence_count = len(_sentences(text))
    confidence = min(0.7, sentence_count * 0.1)  # Max 0.7 for heuristic

    return {"text": summary_text, "confidence": round(confidence, 2)}


def summarize_medium(text):
    """
    Generate medium summary with confidence score.
    Returns: {"text": str, "confidence": float}
    """
    if not text or len(text.strip()) < 10:
        return {"text": "", "confidence": 0.0}

    res = _uniguru(text)
    if isinstance(res, dict) and res.get("summary_medium"):
        summary_text = res.get("summary_medium")
        confidence = 0.85  # High confidence for AI-generated
        return {"text": summary_text, "confidence": confidence}

    # Fallback to heuristic
    summary_text = _fallback_medium(text)
    # Confidence based on text quality
    sentence_count = len(_sentences(text))
    confidence = min(0.65, sentence_count * 0.08)  # Max 0.65 for heuristic

    return {"text": summary_text, "confidence": round(confidence, 2)}
