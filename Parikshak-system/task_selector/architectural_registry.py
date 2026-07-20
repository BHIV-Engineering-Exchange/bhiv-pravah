import logging

logger = logging.getLogger("architectural_registry")

# BCAB/BCAES Canonical Registry
VALID_PROGRAMS = {"BHIV", "TANTRA"}
VALID_DOMAINS = {"governance", "execution", "intelligence", "memory"}
VALID_PRODUCTS = {
    "parikshak", "niyantran", "gurukul", "mitra", "insightflow", "robotics", "blockchain", "saarthi", "gc_shakti", "mdu",
    "vaani tts", "gov-os", "pravah", "bucket"
}

VALID_PLATFORM_SERVICES = {
    "task_orchestration", 
    "evaluation_engine", 
    "learning_delivery", 
    "conversational_ai", 
    "analytics", 
    "robotics_engineering", 
    "blockchain_engineering", 
    "governance_authority", 
    "metadata_discipline",
    # Database strings
    "task review engine",
    "observer portal",
    "audio streamer",
    "security ledger",
    "replay broker",
    "lineage log",
    "universal subsystem",
    "storage layer",
    "authorization gateway",
    "metrics harvester",
    "pac gatekeeper",
    "approvals gateway",
    "oversight console",
    "qa automation suite"
}

VALID_CAPABILITIES = {
    "graph_traversal", 
    "voice_synthesis", 
    "lifecycle_tracking", 
    "rule_validation", 
    "replay_reconstruction", 
    "observability_auditing", 
    "governance_review", 
    "repository_analysis", 
    "task_review",
    "escalation_routing",
    # Database strings
    "submission evaluation",
    "audio synthesis",
    "signature verification",
    "replay verification",
    "lineage archiving",
    "universal capability"
}

# Unified 5-Tier Canonical Taxonomy Mapping
# Format: product -> (Program, Platform_Service, List[Allowed_Domains], List[Owned_Capabilities])
CANONICAL_TAXONOMY = {
    "parikshak": ("BHIV", "evaluation_engine", ["governance", "intelligence"], ["task_review", "repository_analysis", "rule_validation", "voice_synthesis"]),
    "niyantran": ("TANTRA", "task_orchestration", ["governance", "execution"], ["graph_traversal", "workflow_routing", "lifecycle_tracking", "submission evaluation"]),
    "gurukul": ("BHIV", "learning_delivery", ["execution", "memory"], ["lifecycle_tracking"]),
    "mitra": ("BHIV", "conversational_ai", ["intelligence"], ["voice_synthesis"]),
    "insightflow": ("BHIV", "analytics", ["intelligence", "memory"], ["observability_auditing"]),
    "robotics": ("TANTRA", "robotics_engineering", ["execution"], ["repository_analysis"]),
    "blockchain": ("TANTRA", "blockchain_engineering", ["governance", "execution"], ["governance_review"]),
    "saarthi": ("BHIV", "governance_authority", ["governance"], ["escalation_routing"]),
    "gc_shakti": ("BHIV", "governance_authority", ["governance"], ["governance_review"]),
    "mdu": ("BHIV", "metadata_discipline", ["memory"], ["replay_reconstruction", "observability_auditing"]),
    
    # Database mappings
    "vaani tts": ("BHIV", "audio streamer", ["intelligence"], ["audio synthesis", "voice_synthesis"]),
    "gov-os": ("BHIV", "security ledger", ["governance"], ["signature verification", "governance_review"]),
    "pravah": ("BHIV", "replay broker", ["governance", "memory"], ["replay_verification", "replay_reconstruction"]),
    "bucket": ("BHIV", "lineage log", ["memory"], ["lineage archiving", "observability_auditing"])
}

# Add aliases for database products to ensure complete lookups
CANONICAL_TAXONOMY["niyantran core"] = CANONICAL_TAXONOMY["niyantran"]
CANONICAL_TAXONOMY["gov-os security"] = CANONICAL_TAXONOMY["gov-os"]
CANONICAL_TAXONOMY["parikshak signal engine"] = CANONICAL_TAXONOMY["parikshak"]
CANONICAL_TAXONOMY["parikshak rule engine"] = CANONICAL_TAXONOMY["parikshak"]
CANONICAL_TAXONOMY["parikshak decision engine"] = CANONICAL_TAXONOMY["parikshak"]
CANONICAL_TAXONOMY["saarthi interaction portal"] = CANONICAL_TAXONOMY["saarthi"]
CANONICAL_TAXONOMY["niyantran testing"] = CANONICAL_TAXONOMY["niyantran"]
CANONICAL_TAXONOMY["bhiv ecosystem"] = CANONICAL_TAXONOMY["niyantran"]

def validate_task_architecture(
    program: str,
    product: str,
    platform_service: str,
    domain: str,
    capability: str
) -> None:
    """
    Validates a task's architectural details against the canonical BCAB/BCAES registry.
    Raises ValueError on architectural boundary violations or authority drift.
    """
    # Normalize strings
    program = (program or "BHIV").upper().strip()
    product = (product or "").lower().strip()
    platform_service = (platform_service or "").lower().strip()
    domain = (domain or "").lower().strip()
    capability = (capability or "").lower().strip()

    # Normalize aliases of database fields to unified strings
    if product == "niyantran" and platform_service == "task review engine":
        platform_service = "task_orchestration"
    if product == "niyantran" and capability == "submission evaluation":
        capability = "graph_traversal"

    # Verify product exists in taxonomy keys
    if product not in CANONICAL_TAXONOMY:
        raise ValueError(f"HARD_REJECT: Invalid Product '{product}'. Must be one of {VALID_PRODUCTS}")

    # 1. Reject invalid terms
    if program not in VALID_PROGRAMS:
        raise ValueError(f"HARD_REJECT: Invalid Program '{program}'. Must be one of {VALID_PROGRAMS}")
    if platform_service not in VALID_PLATFORM_SERVICES:
        raise ValueError(f"HARD_REJECT: Invalid Platform Service '{platform_service}'. Must be one of {VALID_PLATFORM_SERVICES}")
    if domain not in VALID_DOMAINS:
        raise ValueError(f"HARD_REJECT: Invalid Domain '{domain}'. Must be one of {VALID_DOMAINS}")
    if capability not in VALID_CAPABILITIES:
        raise ValueError(f"HARD_REJECT: Invalid Capability '{capability}'. Must be one of {VALID_CAPABILITIES}")

    # 2. Verify taxonomy combination matches the canonical ownership rules (Architecture Misclassification & Drift)
    canonical = CANONICAL_TAXONOMY[product]
    expected_program, expected_service, expected_domains, owned_capabilities = canonical

    # Map expected service and domain if normalized
    if program != expected_program:
        raise ValueError(
            f"HARD_REJECT: Authority Drift detected. Product '{product}' belongs to Program '{expected_program}', but '{program}' was declared."
        )
    if platform_service != expected_service and platform_service not in (expected_service, "universal subsystem"):
        raise ValueError(
            f"HARD_REJECT: Architectural Misclassification. Product '{product}' maps to Platform Service '{expected_service}', but '{platform_service}' was declared."
        )
    if domain not in expected_domains:
        raise ValueError(
            f"HARD_REJECT: Architectural Misclassification. Product '{product}' belongs to Domains {expected_domains}, but '{domain}' was declared."
        )
    if capability not in owned_capabilities and capability not in (owned_capabilities + ["universal capability"]):
        raise ValueError(
            f"HARD_REJECT: Authority Drift. Product '{product}' does not own Capability '{capability}'."
        )

    logger.info(f"[ARCHITECTURAL REGISTRY] Validation successful for task ({program}/{product}/{platform_service}/{domain}/{capability})")
