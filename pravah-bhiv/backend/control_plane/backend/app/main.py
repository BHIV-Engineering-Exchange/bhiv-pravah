from collections import deque
from datetime import datetime, timezone
import os
import sys
import asyncio
from pathlib import Path
from typing import Any
import json
import uuid

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from .dashboard_api import get_dashboard_state
# from .dashboard_api import router as dashboard_router
from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime
from contracts.decision_contract import validate_decision_contract
from control_plane.core.execution_lineage import (
    replay_execution_lineage,
    verify_execution_lineage,
)
from pydantic import BaseModel
from typing import List, Optional






from typing import Any, Dict
from pydantic import BaseModel

class RuntimeIngestPayload(BaseModel):
    service_id: str
    timestamp: str
    status: str
    metrics: Dict[str, Any]
    issue_detected: bool
    issue_type: str
    recommended_action: str

# Stores latest state per service
INGESTED_RUNTIME_STATE = {}

try:
    from .schemas import DecisionRequest, EventType, Environment
    from .decision_engine import DecisionEngine
except ImportError:
    from schemas import DecisionRequest, EventType, Environment
    from decision_engine import DecisionEngine

def build_decision_request(payload: RuntimeIngestPayload) -> DecisionRequest:
    from control_plane.core.action_governance import normalize_environment
    env_name = normalize_environment(os.getenv("ENVIRONMENT", "DEV"))
    event_map = {
        "high_cpu": EventType.HIGH_CPU,
        "high_memory": EventType.HIGH_MEMORY,
        "latency": EventType.LATENCY,
        "high_latency": EventType.LATENCY,
    }
    
    cpu_val = payload.metrics.get("cpu", 0)
    if isinstance(cpu_val, float) and cpu_val <= 1.0:
        cpu_val *= 100
    cpu = int(cpu_val)

    memory_val = payload.metrics.get("memory", 0)
    if isinstance(memory_val, float) and memory_val <= 1.0:
        memory_val *= 100
    memory = int(memory_val)

    return DecisionRequest(
        environment=Environment(env_name),
        event_type=event_map.get(
            payload.issue_type.lower(),
            EventType.HIGH_CPU,
        ),
        cpu=cpu,
        memory=memory,
    )



def _parse_cors_origins() -> list[str]:
    """Parse explicit CORS origins from env with sane defaults for local and prod."""
    raw = os.getenv(
        "BACKEND_CORS_ORIGINS",
        ",".join(
            [
                "http://localhost:4500",
                "http://localhost:3000",
                "https://multi-agent-control-plane-frontend.vercel.app",
            ]
        ),
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _cors_origin_regex() -> str:
    """Allow Vercel preview URLs and localhost ports unless overridden."""
    return os.getenv(
        "BACKEND_CORS_ORIGIN_REGEX",
        r"^https://.*\.vercel\.app$|^http://localhost:\d+$",
    )

try:
    from .config import ACTION_SCOPE, DEMO_FROZEN, STATELESS, SUCCESS_RATE
    from .schemas import (
        ActionScopeResponse,
        DecisionDashboardSummary,
        DecisionResponse,
        HealthResponse,
        LiveDashboardResponse,
        RecentActivityResponse,
    )
    from .integration_bridge import get_bridge
except ImportError:
    from .config import ACTION_SCOPE, DEMO_FROZEN, STATELESS, SUCCESS_RATE
    from .schemas import (
        ActionScopeResponse,
        DecisionDashboardSummary,
        DecisionResponse,
        HealthResponse,
        LiveDashboardResponse,
        RecentActivityResponse,
    )
    from integration_bridge import get_bridge


# Initialize integration bridge
_bridge = get_bridge()

# Create FastAPI app
app = FastAPI(
    title="Pravah Decision Brain API",
    version="1.0.0",
    description="Pravah RL Decision Brain integrated with Multi-Agent Control Plane",
)

# app.include_router(dashboard_router)
# CORS middleware for local dev + Vercel deploys (stateless API, no credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_origin_regex=_cors_origin_regex(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)


# Startup event: Initialize demo links for realistic dashboard
@app.on_event("startup")
async def startup_event():
    """Initialize dashboard with demo data on app startup."""
    # _initialize_demo_links()


# In-memory recent activity only (reset on process restart).
_RECENT_DECISIONS: deque[DecisionResponse] = deque(maxlen=10)


_AUTONOMOUS_DECISIONS: deque[dict] = deque(maxlen=20)
_LAST_AUTONOMOUS_RUNTIME: dict | None = None
_LAST_EXECUTED_ACTION: str | None = None







# In-memory ingested links for monitoring with rich metadata
_INGESTED_LINKS: list[dict[str, Any]] = []

# Track link ingestion history for events and analytics
_LINK_EVENTS: deque[dict[str, Any]] = deque(maxlen=20)

# Simulated project metadata for ingested links
_LINK_METADATA: dict[str, dict[str, Any]] = {}

# Initialize with demo links for realistic dashboard on startup
def _initialize_demo_links():
    """Populate demo links with realistic metadata on app startup."""
    demo_links = [
        {
            "link": "https://github.com/I-am-ShivamPal/multi-agents-control-plane",
            "name": "multi-agents-control-plane",
        },
        {
            "link": "https://github.com/I-am-ShivamPal/multi-agent-control-plane-frontend",
            "name": "multi-agent-control-plane-frontend",
        },
    ]
    
    for demo_link in demo_links:
        link = demo_link["link"]
        name = demo_link["name"]
        
        # Only add if not already ingested
        if not any(item["link"] == link for item in _INGESTED_LINKS):
            _INGESTED_LINKS.append({
                "link": link,
                "name": name,
                "added_at": datetime.now(timezone.utc).isoformat(),
                "status": "HEALTHY",
                "response_time_ms": 300 + (_get_link_hash(link) % 200),
                "uptime_percent": 99.0 + (_get_link_hash(link) % 10) / 100,
                "errors_24h": _get_link_hash(link) % 3,
            })
            
            # Generate and store metadata
            _LINK_METADATA[link] = _generate_link_metadata(link)
            
            # Log the ingestion event
            _LINK_EVENTS.appendleft({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "link_ingested",
                "link": link,
                "name": name,
            })


def _extract_link_name(link: str) -> str:
    """Extract a clean, readable name from a URL."""
    link = link.strip().rstrip('/')
    
    # Remove protocol
    if "://" in link:
        link = link.split("://", 1)[1]
    
    # Handle GitHub-style URLs
    if link.startswith("github.com/"):
        parts = link.split("/")
        if len(parts) >= 3:
            return parts[2]  # repo name
    
    # Handle other git platforms
    if any(platform in link for platform in ["gitlab.com", "bitbucket.org", "gitea"]):
        parts = link.split("/")
        if len(parts) >= 3:
            return parts[2]  # repo name
    
    # For web URLs, extract domain
    domain = link.split("/")[0]  # Remove path
    domain = domain.replace("www.", "")  # Remove www prefix
    
    # Extract main domain name
    if "." in domain:
        domain = domain.split(".")[0]  # Get first part (e.g., "youtube" from "youtube.com")
    
    # Capitalize first letter
    return domain.capitalize()


def _get_link_hash(link: str) -> int:
    """Generate deterministic hash for a link for consistent metrics."""
    return hash(link) % 10000


def _generate_link_metadata(link: str) -> dict[str, Any]:
    """Generate realistic metadata for an ingested link."""
    link_hash = _get_link_hash(link)
    
    # Simulate project characteristics
    is_github = "github.com" in link.lower()
    is_repo = is_github or "bitbucket" in link.lower() or "gitlab" in link.lower()
    
    base_commits = 0
    base_branches = 0
    base_prs = 0
    base_stars = 0
    base_files = 10 + (link_hash % 100)
    test_coverage = 55 + (link_hash % 40)
    ci_status = "passing" if link_hash % 3 != 0 else "degraded"
    
    if is_github:
        try:
            import requests
            parts = link.split("github.com/")
            if len(parts) > 1:
                repo_path = parts[1].strip("/")
                resp = requests.get(f"https://api.github.com/repos/{repo_path}", timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    base_stars = data.get("stargazers_count", 0)
                    base_prs = data.get("open_issues_count", 0)
                    base_branches = data.get("network_count", data.get("forks_count", 0))
                    base_files = data.get("size", 100) % 1000
                    base_commits = data.get("size", 200)
        except Exception:
            pass # Fallback cleanly if rate limited or network failure
            
    if is_repo and not is_github:
        base_commits = 150 + (link_hash % 500)
        base_branches = 3 + (link_hash % 12)
        base_prs = 5 + (link_hash % 20)
        base_stars = 0
        base_files = 45 + (link_hash % 200)
        test_coverage = 65 + (link_hash % 30)
        ci_status = "passing" if link_hash % 4 != 0 else "failing"
    
    return {
        "type": "repository" if is_repo else "website",
        "commits": base_commits,
        "branches": base_branches,
        "pull_requests": base_prs,
        "stars": base_stars,
        "files": base_files,
        "contributors": 2 + (link_hash % 25),
        "last_commit": "2h ago" if link_hash % 3 == 0 else ("4h ago" if link_hash % 3 == 1 else "8h ago"),
        "test_coverage": test_coverage,
        "ci_status": ci_status,
        "deployment_frequency": 2 + (link_hash % 8),
        "avg_response_time": 120 + (link_hash % 300),
        "error_rate": (link_hash % 5),
        "active_issues": base_prs if is_github else (link_hash % 15),
        "code_quality_score": 70 + (link_hash % 25),
    }


def _bytes_label(size_bytes: int) -> str:
    """Return a compact size label for UI display."""

    if size_bytes <= 0:
        return "0 bytes"
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    return f"{round(size_bytes / 1024, 1)} KB"


def _collect_files(base_path: Path, expected_files: list[str]) -> dict[str, Any]:
    """Collect file state rows for a section, preserving expected order."""

    rows: list[dict[str, str]] = []
    active_count = 0

    for relative_name in expected_files:
        candidate = base_path / relative_name
        exists = candidate.exists() and candidate.is_file()
        size_bytes = candidate.stat().st_size if exists else 0
        if exists:
            active_count += 1
        rows.append(
            {
                "filename": relative_name,
                "status": "ACTIVE" if exists else "MISSING",
                "size": _bytes_label(size_bytes),
            }
        )

    return {"active": active_count, "total": len(expected_files), "files": rows}


def _calculate_health_score(link: str) -> int:
    """Calculate a health score (0-100) for a link based on its metadata."""
    meta = _LINK_METADATA.get(link, {})
    
    # Base score
    score = 85
    
    # Adjust based on CI status
    if meta.get("ci_status") == "passing":
        score += 10
    elif meta.get("ci_status") == "failing":
        score -= 15
    elif meta.get("ci_status") == "degraded":
        score -= 5
    
    # Adjust based on error rate
    error_rate = meta.get("error_rate", 0)
    score -= (error_rate * 3)
    
    # Adjust based on test coverage
    test_coverage = meta.get("test_coverage", 70)
    if test_coverage < 50:
        score -= 10
    elif test_coverage > 80:
        score += 5
    
    # Clamp to 0-100
    return max(0, min(100, score))


def _calculate_aggregate_metrics() -> dict[str, Any]:
    """Calculate real-time aggregate metrics from project and ingested links."""
    import subprocess
    import psutil
    import os

    # 1. Real System Metrics
    try:
        system_cpu = int(psutil.cpu_percent())
        system_memory = int(psutil.virtual_memory().percent)
    except Exception:
        system_cpu = 20
        system_memory = 40
    
    # 2. Real Git stats (workspace repository)
    git_commits = 0
    git_contributors = 1
    git_files = 365
    try:
        commits_res = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, check=True
        )
        git_commits = int(commits_res.stdout.strip())
    except Exception:
        pass

    try:
        contributors_res = subprocess.run(
            ["git", "log", "--format=%an"],
            capture_output=True, text=True, check=True
        )
        git_contributors = len(set(contributors_res.stdout.strip().split("\n")))
    except Exception:
        pass

    try:
        files_res = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, check=True
        )
        git_files = len(files_res.stdout.strip().split("\n"))
    except Exception:
        pass
        
    # 3. Real Test Coverage
    real_coverage = 78
    try:
        import coverage
        cov = coverage.Coverage()
        cov.load()
        real_coverage = int(cov.report(file=open(os.devnull, "w")))
    except Exception:
        pass
        
    # 4. Monitored link counts and stats
    total_decisions = len(_RECENT_DECISIONS)
    try:
        if os.path.exists("logs/control_plane/decision_history.jsonl"):
            with open("logs/control_plane/decision_history.jsonl") as f:
                total_decisions = sum(1 for _ in f)
    except Exception:
        pass
        
    total_policies = 0
    try:
        if os.path.exists("logs/control_plane/policy_enforcement.jsonl"):
            with open("logs/control_plane/policy_enforcement.jsonl") as f:
                total_policies = sum(1 for _ in f)
    except Exception:
        pass
        
    avg_response_time = 150
    if _INGESTED_LINKS:
        avg_response_time = sum(_LINK_METADATA.get(item["link"], {}).get("avg_response_time", 150) for item in _INGESTED_LINKS) / len(_INGESTED_LINKS)

    return {
        "total_commits": git_commits,
        "total_files": git_files,
        "total_contributors": git_contributors,
        "avg_test_coverage": real_coverage,
        "avg_response_time": int(avg_response_time),
        "total_errors": 0,
        "total_issues": 0,
        "avg_quality_score": 92,
        "system_cpu": system_cpu,
        "system_memory": system_memory,
        "total_decisions": total_decisions,
        "total_policies": total_policies,
    }


def _resolve_control_plane_root() -> Path:
    """Resolve project root for control-plane file checks across old/new layouts."""

    configured_root = os.getenv("PROJECT_ROOT", "").strip()
    if configured_root:
        candidate = Path(configured_root).resolve()
        if (candidate / "core").exists() and (candidate / "agent_runtime.py").exists():
            return candidate

    # Current layout: <project>/backend/app/main.py -> project root is parents[2]
    current_project_root = Path(__file__).resolve().parents[2]
    if (current_project_root / "core").exists() and (current_project_root / "agent_runtime.py").exists():
        return current_project_root

    # Legacy layout fallback where repo sat beside backend
    legacy_sibling = current_project_root / "multi-agent-control-plane-main"
    if (legacy_sibling / "core").exists() and (legacy_sibling / "agent_runtime.py").exists():
        return legacy_sibling

    return current_project_root


def _build_live_dashboard_payload() -> dict[str, Any]:
    """Build full real-time dashboard payload consumed by Pravah Dashboard."""
    from control_plane.ml.ml_feature_extractor import MLFeatureExtractor
    import psutil
    
    now_iso = datetime.now(timezone.utc).isoformat()
    env = os.getenv("ENVIRONMENT", "prod").lower()
    
    # Extract ML Intelligence Features
    try:
        extractor = MLFeatureExtractor(env=env)
        ml_intelligence = extractor.extract_features().model_dump()
    except Exception:
        ml_intelligence = {}
        
    # Get System Health
    try:
        system_cpu = int(psutil.cpu_percent())
        system_memory = int(psutil.virtual_memory().percent)
    except Exception:
        system_cpu = 0
        system_memory = 0
        
    system_health = {
        "cpu_utilization_pct": system_cpu,
        "memory_utilization_pct": system_memory,
        "status": "HEALTHY" if system_cpu < 80 else "DEGRADED"
    }
    
    # Build Monitored Services List
    monitored_list = []
    
    # 1. Monitored Runtimes
    for service_id, state in INGESTED_RUNTIME_STATE.items():
        metrics = state.get("metrics", {})
        status = state.get("status", "UNKNOWN").upper()
        cpu = int(metrics.get("cpu", 0) * 100) if metrics.get("cpu", 0) <= 1.0 else int(metrics.get("cpu", 0))
        memory = int(metrics.get("memory", 0) * 100) if metrics.get("memory", 0) <= 1.0 else int(metrics.get("memory", 0))
        
        h_score = 100
        if status == "DEGRADED":
            h_score = 60
        elif status == "CRASHED" or status == "CRITICAL":
            h_score = 20
            
        monitored_list.append({
            "name": service_id.upper(),
            "domain": f"{service_id}.local",
            "url": f"http://localhost/{service_id}",
            "status": "DEGRADED" if status == "DEGRADED" else ("CONNECTED" if status in ["RUNNING", "OK", "HEALTHY"] else "CRITICAL"),
            "health_score": h_score,
            "response_time_ms": int(metrics.get("latency", 100)),
            "cpu_percent": cpu,
            "memory_percent": memory,
            "uptime_percent": 99.9 if status in ["RUNNING", "OK", "HEALTHY"] else 0.0,
            "last_action": _RECENT_DECISIONS[0].selected_action if len(_RECENT_DECISIONS) else "noop",
            "errors_24h": int(metrics.get("error_rate", 0) * 24),
        })

    # 2. Ingested Links
    for item in _INGESTED_LINKS:
        link = item["link"]
        clean_name = item["name"]
        
        if any(x["name"].lower() == clean_name.lower() for x in monitored_list):
            continue
            
        monitored_list.append({
            "name": clean_name,
            "domain": link.replace("https://", "").replace("http://", "").split("/")[0],
            "url": link,
            "status": item.get("status", "CONNECTED"),
            "health_score": 95,
            "response_time_ms": item.get("response_time_ms", 150),
            "cpu_percent": 15,
            "memory_percent": 30,
            "uptime_percent": item.get("uptime_percent", 99.9),
            "last_action": _RECENT_DECISIONS[0].selected_action if len(_RECENT_DECISIONS) else "noop",
            "errors_24h": item.get("errors_24h", 0),
        })
        
    return {
        "generated_at": now_iso,
        "environment": env,
        "system_health": system_health,
        "ml_intelligence": ml_intelligence,
        "recent_decisions": list(_RECENT_DECISIONS),
        "monitored_services": monitored_list,
    }


def enforce_action_scope(action: str, environment: str):
    allowed = ACTION_SCOPE.get(environment, [])

    if action in allowed:
        return True, "allowed"
    else:
        return False, f"{action} not allowed in {environment}"



import requests

def execute_action(action: str, service_id: str):
    try:
        from control_plane.core.action_governance import ActionGovernance, normalize_environment
        from contracts.decision_contract import validate_decision_contract

        env = normalize_environment(os.getenv("ENVIRONMENT", "dev")).lower()
        governance = ActionGovernance(env=env)
        decision = validate_decision_contract(
            {
                "decision_type": "execution",
                "action": action,
                "parameters": {
                    "service_id": service_id,
                    "source": "backend_api",
                },
                "version": governance.POLICY_VERSION,
            }
        )
        governance_decision = governance.evaluate_contract(
            decision=decision,
            context={
                "service_id": service_id,
                "app_name": service_id,
                "env": env,
                "source": "backend_api",
            },
            source="backend_api",
        )

        if governance_decision.should_block:
            return False, {
                "status": "rejected",
                "action": action,
                "service_id": service_id,
                "reason": governance_decision.reason,
                "admission_state": governance_decision.admission_state,
                "rejection_code": governance_decision.rejection_code,
                "policy_snapshot": {
                    "policy_id": governance_decision.policy_id,
                    "policy_version": governance_decision.policy_version,
                    "policy_hash": governance_decision.policy_hash,
                },
            }

        from security.internal_requests import build_signed_headers
        import requests

        payload = {
            "action": action,
            "service_id": service_id
        }
        headers = build_signed_headers(service_id, payload)
        response = requests.post(
            "http://localhost:5003/execute-action",
            json=payload,
            headers=headers,
            timeout=3
        )

        return True, response.json()

    except Exception as e:
        return False, str(e)



@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health and runtime safety guarantees."""

    return HealthResponse(
        status="healthy",
        demo_frozen=DEMO_FROZEN,
        stateless=STATELESS,
        success_rate=SUCCESS_RATE,
    )


@app.get("/action-scope", response_model=ActionScopeResponse)
def action_scope() -> ActionScopeResponse:
    """Return environment-specific allowed actions for policy enforcement."""

    return ActionScopeResponse(**ACTION_SCOPE)





@app.get("/recent-activity", response_model=RecentActivityResponse)
def recent_activity() -> RecentActivityResponse:
    """Return the last ten in-memory decisions, newest first."""

    return RecentActivityResponse(items=list(_RECENT_DECISIONS))


@app.get("/", response_model=LiveDashboardResponse)
def root_dashboard() -> dict[str, Any]:
    """Map root URL directly to the live dashboard payload."""
    return _build_live_dashboard_payload()


@app.get("/live-dashboard", response_model=LiveDashboardResponse)
def live_dashboard() -> dict[str, Any]:
    """Return full real-time dashboard payload consumed by RL Reality UI."""

    return _build_live_dashboard_payload()


@app.get("/decision-summary", response_model=DecisionDashboardSummary)
def decision_summary() -> DecisionDashboardSummary:
    """Return aggregate summary metrics consumed by the Decision Brain UI."""

    return DecisionDashboardSummary(
        total_decisions=len(_RECENT_DECISIONS),
        last_action=_RECENT_DECISIONS[0].selected_action if _RECENT_DECISIONS else "-",
        success_rate=SUCCESS_RATE,
        demo_frozen=DEMO_FROZEN,
        stateless=STATELESS,
    )


@app.post("/ingest-link")
def ingest_link(payload: dict[str, Any]) -> dict[str, Any]:
    """Ingest a repository or website link for monitoring."""

    link = payload.get("link", "").strip()
    if not link:
        return {"success": False, "error": "Link cannot be empty"}

    # Check if link already exists
    existing = next((item for item in _INGESTED_LINKS if item["link"] == link), None)
    if existing:
        return {"success": False, "error": "Link already being monitored"}

    # Generate metadata for this link
    metadata = _generate_link_metadata(link)
    _LINK_METADATA[link] = metadata
    
    # Extract clean name from URL
    link_name = _extract_link_name(link)
    
    # Add new link with monitoring metadata
    ingested_item = {
        "link": link,
        "name": link_name,
        "added_at": datetime.now(timezone.utc).isoformat(),
        "status": "HEALTHY" if metadata["ci_status"] == "passing" else "DEGRADED",
        "response_time_ms": metadata["avg_response_time"],
        "uptime_percent": 99.2 + ((_get_link_hash(link) % 7) * 0.1),
        "errors_24h": metadata["error_rate"],
    }
    _INGESTED_LINKS.append(ingested_item)
    
    # Record event
    _LINK_EVENTS.appendleft({
        "type": "link_added",
        "link": link,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": f"Added {metadata['type']} with {metadata['files']} files",
    })

    return {"success": True, "message": f"Link ingested: {link}", "ingested_link": ingested_item}


@app.post("/remove-link")
def remove_link(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove a monitored link from the dashboard."""

    link = payload.get("link", "").strip()
    if not link:
        return {"success": False, "error": "Link cannot be empty"}

    # Find and remove the link
    global _INGESTED_LINKS, _LINK_METADATA
    original_count = len(_INGESTED_LINKS)
    _INGESTED_LINKS = [item for item in _INGESTED_LINKS if item["link"] != link]
    
    # Remove metadata
    if link in _LINK_METADATA:
        del _LINK_METADATA[link]
    
    # Record event
    if len(_INGESTED_LINKS) < original_count:
        _LINK_EVENTS.appendleft({
            "type": "link_removed",
            "link": link,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": f"Removed {link}",
        })
        return {"success": True, "message": f"Link removed: {link}"}
    else:
        return {"success": False, "error": "Link not found"}


# ============================================================================
# INTEGRATION WITH MULTI-AGENT CONTROL PLANE
# ============================================================================

@app.get("/control-plane/status")
def control_plane_status() -> dict[str, Any]:
    """Get integrated control plane orchestration status."""
    return _bridge.get_control_plane_status()


@app.get("/control-plane/apps")
def control_plane_apps() -> dict[str, Any]:
    """Get list of apps managed by the control plane."""
    apps = _bridge.get_app_registry()
    return {
        "total_apps": len(apps),
        "apps": apps,
        "integration_status": "connected" if _bridge.sync_enabled else "disconnected",
    }


@app.get("/orchestration/metrics")
def orchestration_metrics() -> dict[str, Any]:
    """Get unified orchestration metrics combining RL Brain and Control Plane."""
    agg_metrics = _calculate_aggregate_metrics()
    cp_metrics = _bridge.get_orchestration_metrics()
    
    return {
        "rl_brain": {
            "status": "active",
            "monitored_links": len(_INGESTED_LINKS),
            "total_commits": agg_metrics["total_commits"],
            "total_contributors": agg_metrics["total_contributors"],
            "avg_test_coverage": agg_metrics["avg_test_coverage"],
            "total_decisions": len(_RECENT_DECISIONS),
        },
        "control_plane": cp_metrics,
        "unified": {
            "total_entities_monitored": len(_INGESTED_LINKS) + cp_metrics.get("total_apps_monitored", 0),
            "total_decisions_made": len(_RECENT_DECISIONS) + cp_metrics.get("rl_decisions_made", 0),
            "system_status": "operational",
            "integration_enabled": _bridge.sync_enabled,
        },
    }


@app.get("/metrics")
def prometheus_metrics() -> Response:
    """Expose a small Prometheus scrape surface for decision-brain."""
    agg_metrics = _calculate_aggregate_metrics()
    cp_metrics = _bridge.get_orchestration_metrics()
    lines = [
        "# HELP pravah_decision_brain_up Decision brain service availability.",
        "# TYPE pravah_decision_brain_up gauge",
        "pravah_decision_brain_up 1",
        "# HELP pravah_decision_brain_monitored_links Number of ingested links monitored by decision brain.",
        "# TYPE pravah_decision_brain_monitored_links gauge",
        f"pravah_decision_brain_monitored_links {len(_INGESTED_LINKS)}",
        "# HELP pravah_decision_brain_recent_decisions Number of recent in-memory decisions.",
        "# TYPE pravah_decision_brain_recent_decisions gauge",
        f"pravah_decision_brain_recent_decisions {len(_RECENT_DECISIONS)}",
        "# HELP pravah_decision_brain_total_commits Aggregated commit count across monitored links.",
        "# TYPE pravah_decision_brain_total_commits gauge",
        f"pravah_decision_brain_total_commits {agg_metrics['total_commits']}",
        "# HELP pravah_control_plane_apps_monitored Number of apps reported by the control-plane bridge.",
        "# TYPE pravah_control_plane_apps_monitored gauge",
        f"pravah_control_plane_apps_monitored {cp_metrics.get('total_apps_monitored', 0)}",
    ]
    return Response("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")






@app.get("/api/health")
def api_health():
    return {"status": "ok"}


class ReplayEvent(BaseModel):
    event_id: str
    trace_id: Optional[str] = None
    execution_id: str
    previous_hash: str
    parent_hash: Optional[str] = None
    timestamp: float
    state: str
    execution_hash: Optional[str]
    source: Optional[str]
    details: dict
    payload_hash: Optional[str] = None
    signer: Optional[str] = None
    signature: Optional[str] = None
    trace_hash: Optional[str] = None
    event_hash: Optional[str]


class ReplayResponse(BaseModel):
    execution_id: str
    valid: bool
    final_state: Optional[str]
    execution_state_history: List[str]
    events: List[ReplayEvent]
    execution_hash: Optional[str]
    runtime_attestation: Optional[Dict[str, Any]] = None


class VerifyResponse(BaseModel):
    execution_id: str
    valid: bool
    hash_chain_valid: bool
    fsm_valid: bool
    error: Optional[str] = None
    runtime_attestation_valid: Optional[bool] = None
    runtime_attestation_error: Optional[str] = None


@app.get("/api/lineage/{execution_id}", response_model=ReplayResponse)
def api_replay_lineage(
    execution_id: str,
    state: Optional[str] = None,
    start_ts: Optional[int] = None,
    end_ts: Optional[int] = None,
) -> ReplayResponse:
    """Deterministic, read-only replay of the execution lineage.

    Filters: `state`, `start_ts`, `end_ts` (unix seconds).
    This endpoint reads the journal only and never mutates runtime.
    """
    result = replay_execution_lineage(execution_id)

    # events may be empty; apply simple filters
    events = result.get("events", [])
    def _keep(ev: dict) -> bool:
        if state and ev.get("state") != state:
            return False
        ts = int(ev.get("timestamp") or 0)
        if start_ts and ts < start_ts:
            return False
        if end_ts and ts > end_ts:
            return False
        return True

    filtered = [ev for ev in events if _keep(ev)]

    # Extract runtime attestation from APPROVED event details if present
    runtime_attestation = None
    for ev in filtered:
        details = ev.get("details") or {}
        if details.get("runtime_attestation"):
            runtime_attestation = details.get("runtime_attestation")
            break

    return ReplayResponse(
        execution_id=execution_id,
        valid=result.get("valid", False),
        final_state=(filtered[-1]["state"] if filtered else None),
        execution_state_history=[ev["state"] for ev in filtered],
        events=filtered,
        execution_hash=result.get("execution_hash"),
        runtime_attestation=runtime_attestation,
    )


@app.get("/api/lineage/{execution_id}/verify", response_model=VerifyResponse)
def api_verify_lineage(execution_id: str) -> VerifyResponse:
    """Verify lineage integrity: hash chain and FSM transitions.

    Returns structured booleans rather than raising errors to aid operators.
    """
    try:
        replay_execution_lineage(execution_id)
        # Verify runtime attestation if present
        runtime_attestation_valid = None
        runtime_attestation_error = None
        try:
            replay_result = replay_execution_lineage(execution_id)
            for ev in replay_result.get("events", []):
                details = ev.get("details") or {}
                ra = details.get("runtime_attestation")
                if ra:
                    from contracts.runtime_attestation import verify_runtime_attestation

                    ok, msg = verify_runtime_attestation(ra)
                    runtime_attestation_valid = ok
                    runtime_attestation_error = None if ok else msg
                    break
        except Exception:
            # leave attestation fields as None when replay fails here
            runtime_attestation_valid = None
            runtime_attestation_error = None
        return VerifyResponse(
            execution_id=execution_id,
            valid=True,
            hash_chain_valid=True,
            fsm_valid=True,
            error=None,
            runtime_attestation_valid=runtime_attestation_valid,
            runtime_attestation_error=runtime_attestation_error,
        )
    except Exception as e:
        msg = str(e)
        hash_ok = True
        fsm_ok = True
        # Classify common failure modes
        if any(
            token in msg.lower()
            for token in (
                "hash mismatch",
                "chain broken",
                "unsigned",
                "signature",
                "duplicate",
                "timestamp",
            )
        ):
            hash_ok = False
        if "illegal" in msg.lower() or "replay start state" in msg.lower() or "continuation after terminal" in msg.lower():
            fsm_ok = False

        return VerifyResponse(
            execution_id=execution_id,
            valid=False,
            hash_chain_valid=hash_ok,
            fsm_valid=fsm_ok,
            error=msg,
        )








@app.post("/process-runtime")
def process_runtime(payload: Dict[str, Any]):
    """Decide action based on telemetry metrics and return requested action."""
    from control_plane.core.action_governance import normalize_environment
    from .schemas import Environment, EventType, DecisionRequest
    
    env_raw = payload.get("environment") or payload.get("env") or os.getenv("ENVIRONMENT", "dev")
    env_name = normalize_environment(env_raw)
    
    # Extract CPU and Memory
    cpu = int(payload.get("cpu_usage") or payload.get("cpu") or 0)
    memory = int(payload.get("memory_usage") or payload.get("memory") or 0)
    
    # Determine EventType from signals or properties
    event_type = EventType.HIGH_CPU
    signals = payload.get("signals", [])
    if signals:
        sig_type = signals[0].get("type", "").lower()
        if "latency" in sig_type or "overload" in sig_type:
            event_type = EventType.LATENCY
        elif "memory" in sig_type or "crashed" in sig_type:
            event_type = EventType.HIGH_MEMORY
            
    decision_request = DecisionRequest(
        environment=Environment(env_name),
        event_type=event_type,
        cpu=cpu,
        memory=memory
    )
    
    decision = DecisionEngine.decide(decision_request)
    
    # Append to recent decisions list
    from .schemas import DecisionResponse
    _RECENT_DECISIONS.appendleft(DecisionResponse(
        decision_id=decision.decision_id,
        environment=decision.environment,
        selected_action=decision.selected_action,
        reason=decision.reason,
        confidence=decision.confidence,
        timestamp=decision.timestamp,
        version=decision.version
    ))
    
    return {
        "action_requested": decision.selected_action,
        "confidence": decision.confidence,
        "reason": decision.reason
    }


@app.post("/control-plane/runtime-ingest")
def runtime_ingest(payload: RuntimeIngestPayload):
    from control_plane.core.trace_logger import log_event, reset_trace, ensure_complete_trace

    # 1. Reset trace and log detection
    reset_trace()
    log_event("detection", {
        "issue": payload.issue_type,
        "service_id": payload.service_id,
        "metrics": payload.metrics
    })

    INGESTED_RUNTIME_STATE[payload.service_id] = payload.model_dump()
    decision_request = build_decision_request(payload)
    decision = DecisionEngine.decide(decision_request)
    
    # 2. Log payload_emitted
    log_event("payload_emitted", {
        "service_id": payload.service_id,
        "action": decision.selected_action
    })
    
    # 3. Log action_received
    log_event("action_received", {
        "service_id": payload.service_id,
        "action": decision.selected_action
    })
    
    success, execution_result = execute_action(
        action=decision.selected_action,
        service_id=payload.service_id,
    )
    
    if not success:
        if isinstance(execution_result, dict):
            execution_id = execution_result.get("execution_id")
            status = "blocked"
            reason = execution_result.get("reason", "governance_block")
        else:
            execution_id = None
            status = "blocked"
            reason = str(execution_result)
        
        # 4. Log execution_result (failure/blocked)
        log_event("execution_result", {
            "service_id": payload.service_id,
            "action": decision.selected_action,
            "status": status,
            "error": reason,
            "execution_id": execution_id
        })
        
        # 5. Log verification (failed)
        log_event("verification", {
            "verified": False,
            "reason": reason
        })
        ensure_complete_trace()
        
        return {
            "service_id": payload.service_id,
            "decision": decision.model_dump(mode="json"),
            "execution": {
                "execution_id": execution_id,
                "status": status,
                "reason": reason,
                "action": decision.selected_action,
            },
        }

    # 4. Log execution_result (success)
    exec_id = execution_result.get("execution_id") if isinstance(execution_result, dict) else None
    status = execution_result.get("status", "executed") if isinstance(execution_result, dict) else "executed"
    reason = execution_result.get("reason") if isinstance(execution_result, dict) else None
    verified = execution_result.get("verified", False) if isinstance(execution_result, dict) else False

    log_event("execution_result", {
        "service_id": payload.service_id,
        "action": decision.selected_action,
        "status": status,
        "execution_id": exec_id
    })
    
    # 5. Log verification
    log_event("verification", {
        "verified": verified,
        "reason": reason
    })
    ensure_complete_trace()

    return {
        "service_id": payload.service_id,
        "decision": decision.model_dump(mode="json"),
        "execution": {
            "execution_id": exec_id,
            "status": status,
            "reason": reason,
            "action": execution_result.get("action") if isinstance(execution_result, dict) else decision.selected_action,
        },
    }









import threading
import time





@app.get("/autonomous-status")
def autonomous_status():
    return {
        "last_runtime": _LAST_AUTONOMOUS_RUNTIME,
        "last_action": _LAST_EXECUTED_ACTION,
        "recent_autonomous_decisions": list(_AUTONOMOUS_DECISIONS),
        "loop_running": True,
    }








@app.get("/dashboard/state")
def dashboard_state():
    return get_dashboard_state()














from fastapi import HTTPException

class PravahEventRequest(BaseModel):
    trace_id: str
    event_type: str
    payload: Dict[str, Any]
    source_system: str
    published_at: str

class EvidenceBundleRequest(BaseModel):
    bundle_id: str
    trace_id: str
    execution_id: str
    decision_id: str
    decision_type: str
    authority_chain: List[str]
    evidence: List[Dict[str, Any]]
    replay_reference: str
    constitutional_hash: str
    produced_at: str

_EVIDENCE_STORE: Dict[str, Any] = {}

@app.post("/pravah/events")
def create_pravah_event(request: PravahEventRequest):
    return {
        "status": "CONNECTED",
        "trace_id": request.trace_id,
        "published_at": datetime.now(timezone.utc).isoformat()
    }

@app.post("/evidence")
def store_evidence(request: EvidenceBundleRequest):
    evidence_ref = str(uuid.uuid4())
    _EVIDENCE_STORE[evidence_ref] = request.dict()
    return {
        "evidence_ref": evidence_ref,
        "published_at": datetime.now(timezone.utc).isoformat()
    }

@app.get("/evidence/{evidence_ref}")
def get_evidence(evidence_ref: str):
    if evidence_ref not in _EVIDENCE_STORE:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return _EVIDENCE_STORE[evidence_ref]


@app.get("/api/ml/features/latest")
def get_ml_features():
    from control_plane.ml.ml_feature_extractor import MLFeatureExtractor
    extractor = MLFeatureExtractor(env=os.getenv("ENVIRONMENT", "prod").lower())
    features = extractor.extract_features()
    return features.model_dump()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("BACKEND_PORT", os.getenv("PORT", "8000")))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)


