from typing import List, Dict, Any

def classify_truth_level(signals: List[Dict[str, Any]], divergence_score: float) -> int:
    """
    Classifies the structural truth level (0-4) based on signals and divergence.
    """
    n = len(signals)
    
    # Level 1: Single-source claim
    if n == 1:
        return 1
    
    # Level 0: Insufficient data
    if n == 0:
        return 0
        
    # Check for contradiction first
    # Truth level must not override contradiction (as per PDF)
    if divergence_score > 0:
        return 3 # Structured contradiction
        
    # Alignment cases
    unique_sources = set(s.get("source_id", "unknown") for s in signals)
    num_sources = len(unique_sources)
    
    # Level 4: Convergent corroboration 
    # (Multiple sources agreeing, high diversity)
    if num_sources >= 3:
        return 4
        
    # Level 2: Multi-source alignment
    # (At least 2 unique sources agreeing)
    if num_sources >= 2:
        return 2
        
    # Fallback to Level 1 if multiple signals from same single source
    return 1
