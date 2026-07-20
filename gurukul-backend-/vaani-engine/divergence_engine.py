from typing import List, Dict, Any

def compute_divergence(signals: List[Dict[str, Any]]) -> float:
    """
    Computes structural divergence score (0-1).
    D = (Unique_Statements - 1) / (Total_Signals - 1)
    """
    if not signals or len(signals) <= 1:
        return 0.0
    
    # Extract statements and find unique ones
    statements = [s.get("statement", "").strip() for s in signals]
    unique_statements = set(statements)
    
    n = len(signals)
    u = len(unique_statements)
    
    # Calculate score
    score = (u - 1) / (n - 1)
    return round(score, 4)

def generate_contradiction_map(signals: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Creates a map of which sources are providing which unique statements.
    """
    statement_map = {}
    for s in signals:
        stmt = s.get("statement", "").strip()
        source = s.get("source_id", "unknown")
        
        if stmt not in statement_map:
            statement_map[stmt] = []
        statement_map[stmt].append(source)
    
    return statement_map
