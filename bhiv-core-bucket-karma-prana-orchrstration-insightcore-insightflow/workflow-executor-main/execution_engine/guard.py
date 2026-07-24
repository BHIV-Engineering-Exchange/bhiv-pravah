def should_execute(decision: str) -> bool:
    """
    Execution is allowed only when decision is exactly 'workflow'
    """
    return decision == "workflow"
