import math

# Financial-specific sentiment lexicons
POS = {"good","great","positive","benefit","growth","optimistic","gain","win","strong","record","surge","rise","improve","success","joy","happy","profit","bullish","rally","upbeat","expansion"}
NEG = {"bad","poor","negative","loss","drop","decline","fall","weak","crisis","fear","warn","risk","fail","collapse","urgent","emergency","bearish","recession","bankrupt","fraud","scandal"}
URGENT = {"breaking","urgent","emergency","crisis","alert","deadline"}

def _score(text):
    """
    Calculate sentiment score deterministically.
    Returns: (label, score, tone)
    - label: "positive" | "negative" | "neutral"
    - score: float between -1.0 and 1.0
    - tone: "urgent" | "joyful" | "calm"
    """
    t = (text or "").lower()
    p = sum(1 for w in POS if w in t)
    n = sum(1 for w in NEG if w in t)
    
    # Calculate raw score (-1.0 to 1.0)
    total = p + n
    if total == 0:
        raw_score = 0.0
    else:
        raw_score = (p - n) / total
    
    # Determine label
    if raw_score > 0.1:
        pol = "positive"
    elif raw_score < -0.1:
        pol = "negative"
    else:
        pol = "neutral"
    
    # Calculate confidence (0.0 to 1.0)
    conf = min(1.0, total / 8.0) if total > 0 else 0.3
    
    # Determine tone
    if any(w in t for w in URGENT):
        tone = "urgent"
    elif p > n and p > 0:
        tone = "joyful"
    else:
        tone = "calm"
    
    return pol, round(raw_score, 2), tone

def analyze(text):
    """
    Analyze sentiment and return contract-compatible result.
    Returns: {"label": str, "score": float, "confidence": float, "tone": str}
    """
    pol, score, tone = _score(text)
    conf = min(1.0, abs(score) + 0.3)  # Confidence based on score magnitude
    
    return {
        "label": pol,
        "score": score,
        "confidence": round(conf, 2),
        "tone": tone
    }