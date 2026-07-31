#!/usr/bin/env python3
"""
Pravah Bhiv Observer Server
Lightweight FastAPI server that provides execution visibility into observed services.
Pravah observes - it does not own - the execution of these systems.

Runs on port 8600 (default).
"""

import os
import sys
import time
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# Configuration from environment (set by observer_launcher.py)
# ---------------------------------------------------------------------------
OBSERVER_PORT = int(os.getenv("PRAVAH_OBSERVER_PORT", "8600"))
CRM_API_URL = os.getenv("PRAVAH_CRM_API", "http://localhost:8001")
MAIN_API_URL = os.getenv("PRAVAH_MAIN_API", "http://localhost:8000")
CRM_DASHBOARD_URL = os.getenv("PRAVAH_CRM_DASHBOARD", "http://localhost:8501")
MAIN_DASHBOARD_URL = os.getenv("PRAVAH_MAIN_DASHBOARD", "http://localhost:8502")
CONTROL_PLANE_URL = os.getenv("PRAVAH_CONTROL_PLANE", "http://localhost:7000")
# Gurukul backend — Pravah observes, does not own
# Gurukul backend — Pravah observes, does not own
GURUKUL_API_URL = os.getenv("PRAVAH_GURUKUL_API", "https://gurukul-up9j.onrender.com")
# INFIVERSE HR Platform gateway — Pravah observes, does not own
HR_API_URL = os.getenv("PRAVAH_HR_API", "http://localhost:8000")
# Parikshak System API — Pravah observes, does not own
PARIKSHAK_API_URL = os.getenv("PRAVAH_PARIKSHAK_API", "http://localhost:8080")
# Prompt Runner API — Pravah observes, does not own
PROMPT_RUNNER_API_URL = os.getenv("PRAVAH_PROMPT_RUNNER_API", "http://localhost:8001")
# Trade Bot API — Pravah observes, does not own
TRADE_BOT_API_URL = os.getenv("PRAVAH_TRADE_BOT_API", "http://localhost:8002")
# TTG API — Pravah observes, does not own
TTG_API_URL = os.getenv("PRAVAH_TTG_API", "http://localhost:3005")
# UniGuru AI API — Pravah observes, does not own
UNIGURU_API_URL = os.getenv("PRAVAH_UNIGURU_API", "https://uniguru-ai-2.onrender.com")
# Workflow Blackhole API — Pravah observes, does not own
WORKFLOW_BLACKHOLE_API_URL = os.getenv("PRAVAH_WORKFLOW_BLACKHOLE_API", "http://localhost:5005")
# Blockchain API — Pravah observes, does not own
BLOCKCHAIN_API_URL = os.getenv("PRAVAH_BLOCKCHAIN_API", "http://localhost:8004")

# BHIV Runtimes — Pravah observes, does not own
BHIV_KARMA_URL = os.getenv("PRAVAH_BHIV_KARMA", "http://localhost:8000")
BHIV_BUCKET_URL = os.getenv("PRAVAH_BHIV_BUCKET", "http://localhost:8001")
BHIV_CORE_URL = os.getenv("PRAVAH_BHIV_CORE", "http://localhost:8002")
BHIV_WORKFLOW_URL = os.getenv("PRAVAH_BHIV_WORKFLOW", "http://localhost:8003")
BHIV_UAO_URL = os.getenv("PRAVAH_BHIV_UAO", "http://localhost:8004")
BHIV_INSIGHT_CORE_URL = os.getenv("PRAVAH_BHIV_INSIGHT_CORE", "http://localhost:8005")
BHIV_INSIGHT_FLOW_BRIDGE_URL = os.getenv("PRAVAH_BHIV_INSIGHT_FLOW_BRIDGE", "http://localhost:8006")
BHIV_INSIGHT_FLOW_BACKEND_URL = os.getenv("PRAVAH_BHIV_INSIGHT_FLOW_BACKEND", "http://localhost:8007")
BHIV_KESHAV_URL = os.getenv("PRAVAH_BHIV_KESHAV", "http://localhost:5000")
BHIV_SARATHI_URL = os.getenv("PRAVAH_BHIV_SARATHI", "https://sarathi-9n5g.onrender.com")



# ---------------------------------------------------------------------------
# In-memory observation store
# ---------------------------------------------------------------------------
MAX_EVENTS = 200

observation_store: Dict[str, Any] = {
    "services": {},
    "events": [],
    "started_at": datetime.utcnow().isoformat(),
    "poll_count": 0,
}

store_lock = threading.Lock()


def _record_event(service: str, status: str, detail: str = "", latency_ms: float = 0):
    """Append an observation event (thread-safe)."""
    event = {
        "ts": datetime.utcnow().isoformat(),
        "service": service,
        "status": status,
        "detail": detail,
        "latency_ms": round(latency_ms, 1),
    }
    with store_lock:
        observation_store["events"].append(event)
        if len(observation_store["events"]) > MAX_EVENTS:
            observation_store["events"] = observation_store["events"][-MAX_EVENTS:]


def _probe_service(name: str, health_url: str, url: str):
    """Probe a single service endpoint and record the result."""
    import requests as _req

    start = time.time()
    try:
        resp = _req.get(health_url, timeout=3)
        latency = (time.time() - start) * 1000
        ok = resp.status_code < 400
        detail = ""
        try:
            detail = json.dumps(resp.json())[:200]
        except Exception:
            detail = resp.text[:200]
        status = "healthy" if ok else "degraded"
    except _req.ConnectionError:
        latency = (time.time() - start) * 1000
        status = "unreachable"
        detail = "connection refused"
    except _req.Timeout:
        latency = (time.time() - start) * 1000
        status = "timeout"
        detail = "request timed out"
    except Exception as exc:
        latency = (time.time() - start) * 1000
        status = "error"
        detail = str(exc)[:200]

    with store_lock:
        observation_store["services"][name] = {
            "url": url,
            "status": status,
            "latency_ms": round(latency, 1),
            "detail": detail,
            "last_checked": datetime.utcnow().isoformat(),
        }

    _record_event(name, status, detail, latency)


def _poll_loop(interval: float = 10.0):
    """Background thread that continuously polls observed services.
    Pravah observes — it does not own — the execution of these systems.
    All probes are read-only GET requests to health endpoints.
    """
    from concurrent.futures import ThreadPoolExecutor
    
    while True:
        services = {
            "gurukul-backend": {
                "url": GURUKUL_API_URL,
                "health_url": f"{GURUKUL_API_URL}/health"
            },
            "infiverse-hr-platform": {
                "url": HR_API_URL,
                "health_url": f"{HR_API_URL}/health"
            },
            "parikshak-system": {
                "url": PARIKSHAK_API_URL,
                "health_url": f"{PARIKSHAK_API_URL}/health"
            },
            "crm-api": {
                "url": CRM_API_URL,
                "health_url": f"{CRM_API_URL}/health"
            },

            "control-plane": {
                "url": CONTROL_PLANE_URL,
                "health_url": f"{CONTROL_PLANE_URL}/api/health"
            },
            "prompt-runner01": {
                "url": PROMPT_RUNNER_API_URL,
                "health_url": f"{PROMPT_RUNNER_API_URL}/health"
            },

            "ttg": {
                "url": TTG_API_URL,
                "health_url": f"{TTG_API_URL}/health"
            },
            "uniguru_ai": {
                "url": UNIGURU_API_URL,
                "health_url": f"{UNIGURU_API_URL}/health"
            },
            "workflow-blackhole": {
                "url": WORKFLOW_BLACKHOLE_API_URL,
                "health_url": f"{WORKFLOW_BLACKHOLE_API_URL}"
            },

            "bhiv-masterdb-ingestion-certification-service": {
                "url": os.getenv("PRAVAH_MASTERDB_API", "https://masterdb-ingestion-certification-service.onrender.com"),
                "health_url": f"{os.getenv('PRAVAH_MASTERDB_API', 'https://masterdb-ingestion-certification-service.onrender.com')}/health"
            },
            "bhiv-Mitra": {
                "url": os.getenv("PRAVAH_MITRA_API", "http://localhost:8000"),
                "health_url": f"{os.getenv('PRAVAH_MITRA_API', 'http://localhost:8000')}/health"
            },

            "bhiv-bucket": {
                "url": BHIV_BUCKET_URL,
                "health_url": f"{BHIV_BUCKET_URL}/health"
            },


            "bhiv-insight-core": {
                "url": BHIV_INSIGHT_CORE_URL,
                "health_url": f"{BHIV_INSIGHT_CORE_URL}/health"
            },
            "bhiv-insight-flow-bridge": {
                "url": BHIV_INSIGHT_FLOW_BRIDGE_URL,
                "health_url": f"{BHIV_INSIGHT_FLOW_BRIDGE_URL}/health"
            },
            "bhiv-insight-flow-backend": {
                "url": BHIV_INSIGHT_FLOW_BACKEND_URL,
                "health_url": f"{BHIV_INSIGHT_FLOW_BACKEND_URL}/health"
            },
            "bhiv-keshav-4": {
                "url": BHIV_KESHAV_URL,
                "health_url": f"{BHIV_KESHAV_URL}/health"
            },
            "bhiv-sarathi": {
                "url": BHIV_SARATHI_URL,
                "health_url": f"{BHIV_SARATHI_URL}/health/deep"
            },
            "bhiv-hr-agent": {
                "url": os.getenv("PRAVAH_BHIV_HR_AGENT", "http://localhost:8000"),
                "health_url": f"{os.getenv('PRAVAH_BHIV_HR_AGENT', 'http://localhost:8000')}/health"
            },
            "bhiv-hr-langgraph": {
                "url": os.getenv("PRAVAH_BHIV_HR_LANGGRAPH", "http://localhost:8000"),
                "health_url": f"{os.getenv('PRAVAH_BHIV_HR_LANGGRAPH', 'http://localhost:8000')}/health"
            },
            "shakti-gc-infra": {
                "url": os.getenv("PRAVAH_SHAKTI_GC_INFRA", "http://localhost:8000"),
                "health_url": f"{os.getenv('PRAVAH_SHAKTI_GC_INFRA', 'http://localhost:8000')}/governance/health"
            },
            "samruddhi": {
                "url": os.getenv("PRAVAH_SAMRUDDHI_API", "http://localhost:8000"),
                "health_url": f"{os.getenv('PRAVAH_SAMRUDDHI_API', 'http://localhost:8000')}/tools/health"
            },
            "samruddhi-hft": {
                "url": os.getenv("PRAVAH_SAMRUDDHI_HFT", "http://localhost:8000"),
                "health_url": f"{os.getenv('PRAVAH_SAMRUDDHI_HFT', 'http://localhost:8000')}/api/health"
            },
            "bhiv-mdu-api": {
                "url": os.getenv("PRAVAH_MDU_API", "http://localhost:8000"),
                "health_url": f"{os.getenv('PRAVAH_MDU_API', 'http://localhost:8000')}/health"
            },
            "insightbridge-phase4-demo": {
                "url": os.getenv("PRAVAH_INSIGHTBRIDGE_DEMO_API", "http://localhost:8000"),
                "health_url": f"{os.getenv('PRAVAH_INSIGHTBRIDGE_DEMO_API', 'http://localhost:8000')}/health"
            },
            "core-integrator-collaborative": {
                "url": os.getenv("PRAVAH_CORE_INTEGRATOR_API", "https://core-integrator-collaborative.onrender.com"),
                "health_url": f"{os.getenv('PRAVAH_CORE_INTEGRATOR_API', 'https://core-integrator-collaborative.onrender.com')}/openapi.json"
            },
        }
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for svc_name, svc_cfg in services.items():
                futures.append(executor.submit(_probe_service, svc_name, svc_cfg["health_url"], svc_cfg["url"]))
            for f in futures:
                f.result() # Wait for all to complete
                
        with store_lock:
            observation_store["poll_count"] += 1
        time.sleep(interval)



# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Pravah Bhiv Observer",
    description="Execution visibility layer - observe, don't own.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def start_background_poller():
    poller = threading.Thread(target=_poll_loop, args=(10.0,), daemon=True)
    poller.start()
    print("[Pravah Observer] Background poller started on FastAPI startup (10s interval)")


# ---- JSON API endpoints ---------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "service": "pravah-observer", "ts": datetime.utcnow().isoformat()}


@app.get("/api/status")
def api_status():
    with store_lock:
        return JSONResponse(content={
            "started_at": observation_store["started_at"],
            "poll_count": observation_store["poll_count"],
            "services": observation_store["services"],
        })


@app.get("/api/events")
def api_events(limit: int = 50):
    with store_lock:
        events = list(reversed(observation_store["events"]))[:limit]
    return JSONResponse(content={"events": events, "total": len(events)})


@app.get("/api/lineage")
def api_lineage():
    evidence_path = os.path.join(os.path.dirname(__file__), "data", "evidence_bundles.json")
    if not os.path.exists(evidence_path):
        return JSONResponse(content={"lineages": []})
    try:
        with open(evidence_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            bundles = list(data.values())
            return JSONResponse(content={"lineages": bundles})
    except Exception as e:
        return JSONResponse(content={"error": str(e), "lineages": []}, status_code=500)

@app.get("/api/metrics")
def api_metrics():
    from fastapi.responses import Response
    with store_lock:
        poll_count = observation_store["poll_count"]
        services = observation_store["services"]
        services_count = len(services)
        healthy_count = sum(1 for s in services.values() if s.get("status") == "healthy")
        degraded_count = sum(1 for s in services.values() if s.get("status") == "degraded")
        
    metrics = [
        f"# HELP observer_poll_count_total Total number of active polling loops executed",
        f"# TYPE observer_poll_count_total counter",
        f"observer_poll_count_total {poll_count}",
        f"# HELP observer_monitored_services_total Total number of monitored services",
        f"# TYPE observer_monitored_services_total gauge",
        f"observer_monitored_services_total {services_count}",
        f"# HELP observer_healthy_services_total Number of healthy services observed",
        f"# TYPE observer_healthy_services_total gauge",
        f"observer_healthy_services_total {healthy_count}",
        f"# HELP observer_degraded_services_total Number of degraded services observed",
        f"# TYPE observer_degraded_services_total gauge",
        f"observer_degraded_services_total {degraded_count}"
    ]
    
    content = "\n".join(metrics) + "\n"
    return Response(content=content, media_type="text/plain; version=0.0.4")


@app.post("/api/ingest")
async def ingest_event(request: Request):
    """Accept external telemetry events pushed by observed services."""
    body = await request.json()
    _record_event(
        service=body.get("service", "unknown"),
        status=body.get("status", "info"),
        detail=json.dumps(body.get("data", {}))[:300],
    )
    return {"accepted": True}


# ---- HTML Dashboard -------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return _render_dashboard_html()


def _render_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Pravah Bhiv - Ecosystem Observability Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#05070f;--surface:#0b0d19;--card:rgba(18,22,38,0.7);--border:rgba(255,255,255,0.06);
  --text:#f0f4fc;--muted:#7e8b9f;--accent:linear-gradient(135deg, #6c35ff 0%, #00e5ff 100%);
  --accent-color:#6c35ff;--accent2:#00e5ff;
  --green:#00e676;--red:#ff1744;--yellow:#ffea00;--blue:#2979ff;
  --glow-green:rgba(0,230,118,0.15);--glow-red:rgba(255,23,68,0.15);--glow-yellow:rgba(255,234,0,0.15);
}
body{font-family:'Inter',sans-serif;background-color:var(--bg);background-image:radial-gradient(circle at 5% 10%, rgba(108,53,255,0.06) 0%, transparent 50%), radial-gradient(circle at 95% 90%, rgba(0,229,255,0.06) 0%, transparent 50%);color:var(--text);min-height:100vh;overflow-x:hidden}
.header{
  background:rgba(11,13,25,0.85);
  backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  border-bottom:1px solid var(--border);padding:20px 40px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:100;
}
.header h1{font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;letter-spacing:-.8px;background:var(--accent);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header h1 span{font-weight:400;color:var(--muted);-webkit-text-fill-color:var(--muted)}
.header .meta{font-size:.85rem;color:var(--muted);font-weight:500;display:flex;align-items:center;gap:12px}
#clock{background:rgba(255,255,255,0.03);padding:6px 14px;border-radius:30px;border:1px solid var(--border);color:var(--text);font-family:monospace;letter-spacing:0.5px}
.tabs{display:flex;gap:8px;margin-bottom:24px;border-bottom:1px solid var(--border);padding-bottom:12px}
.tab-btn{background:none;border:none;color:var(--muted);font-family:'Outfit',sans-serif;font-size:.95rem;font-weight:600;padding:8px 18px;border-radius:8px;cursor:pointer;transition:all 0.3s ease}
.tab-btn:hover{color:var(--text);background:rgba(255,255,255,0.02)}
.tab-btn.active{color:var(--accent2);background:rgba(0,229,255,0.08);border:1px solid rgba(0,229,255,0.2);box-shadow:0 0 15px rgba(0,229,255,0.08)}
.tab-content{display:none}
.tab-content.active{display:block}
.badge{display:inline-block;padding:4px 12px;border-radius:30px;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;transition:all 0.3s ease}
.badge.healthy{background:rgba(0,230,118,.12);color:var(--green);border:1px solid rgba(0,230,118,0.2);box-shadow:0 0 10px var(--glow-green)}
.badge.unreachable,.badge.error{background:rgba(255,23,68,0.12);color:var(--red);border:1px solid rgba(255,23,68,0.2);box-shadow:0 0 10px var(--glow-red)}
.badge.degraded,.badge.timeout{background:rgba(255,234,0,.12);color:var(--yellow);border:1px solid rgba(255,234,0,0.2);box-shadow:0 0 10px var(--glow-yellow)}
.badge.info{background:rgba(124,77,255,.12);color:var(--accent-color);border:1px solid rgba(124,77,255,0.2)}
.container{max-width:1440px;margin:0 auto;padding:32px 24px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:24px;margin-bottom:32px}
.card{background:var(--card);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid var(--border);border-radius:16px;padding:24px;transition:all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);box-shadow:0 8px 32px 0 rgba(0,0,0,0.2)}
.card:hover{transform:translateY(-4px);border-color:rgba(108,53,255,0.3);box-shadow:0 12px 30px rgba(108,53,255,0.1)}
.card h3{font-family:'Outfit',sans-serif;font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between}
.svc-name{font-family:'Outfit',sans-serif;font-size:1.3rem;font-weight:700;margin-bottom:6px;color:#ffffff;letter-spacing:-0.3px}
.svc-url{font-size:.72rem;color:var(--muted);word-break:break-all;font-family:monospace;background:rgba(0,0,0,0.2);padding:6px 10px;border-radius:6px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.02)}
.svc-latency{font-family:'Outfit',sans-serif;font-size:1.8rem;font-weight:800;color:var(--accent2);margin:12px 0 8px;display:flex;align-items:baseline;gap:4px}
.svc-latency small{font-size:.8rem;color:var(--muted);font-weight:400;font-family:'Inter',sans-serif}
.events-card{background:var(--card);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid var(--border);border-radius:16px;padding:28px;box-shadow:0 8px 32px 0 rgba(0,0,0,0.2)}
.events-card h3{font-family:'Outfit',sans-serif;font-size:1rem;font-weight:700;margin-bottom:20px;color:#ffffff;letter-spacing:-0.3px;display:flex;align-items:center;justify-content:space-between}
.events-card h3 span{font-size:0.72rem;color:var(--muted);font-weight:400;background:rgba(255,255,255,0.03);padding:4px 10px;border-radius:20px;border:1px solid var(--border)}
.events-table-wrapper{overflow-x:auto}
.events-table{width:100%;border-collapse:collapse;text-align:left}
.events-table th,.events-table td{padding:14px 18px;border-bottom:1px solid var(--border);font-size:.8rem}
.events-table th{color:var(--muted);font-weight:600;text-transform:uppercase;font-size:.72rem;letter-spacing:1.2px;background:rgba(255,255,255,0.01)}
.events-table td{color:var(--text)}
.events-table tr{transition:background-color 0.2s ease}
.events-table tr:hover{background:rgba(108,53,255,0.02)}
.detail-cell{max-width:350px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted);font-family:monospace;font-size:0.75rem}
.pulse{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px;position:relative;vertical-align:middle}
.pulse.healthy{background:var(--green);box-shadow:0 0 8px var(--green)}
.pulse.unreachable,.pulse.error{background:var(--red);box-shadow:0 0 8px var(--red)}
.pulse.degraded,.pulse.timeout{background:var(--yellow);box-shadow:0 0 8px var(--yellow)}
.pulse::after{content:'';width:100%;height:100%;border-radius:50%;position:absolute;top:0;left:0;animation:pulse-ring 2.5s infinite;opacity:0.3}
.pulse.healthy::after{border:1px solid var(--green)}
.pulse.unreachable::after,.pulse.error::after{border:1px solid var(--red)}
.pulse.degraded::after,.pulse.timeout::after{border:1px solid var(--yellow)}
@keyframes pulse-ring{0%{transform:scale(1);opacity:0.3}50%{transform:scale(2.2);opacity:0}100%{transform:scale(1);opacity:0}}
.footer{text-align:center;padding:24px;color:var(--muted);font-size:.75rem;border-top:1px solid var(--border);margin-top:48px;letter-spacing:0.5px}
.stat-row{display:flex;gap:20px;margin-bottom:32px;flex-wrap:wrap}
.stat-box{flex:1;min-width:200px;background:var(--card);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid var(--border);border-radius:16px;padding:20px;text-align:center;box-shadow:0 8px 32px 0 rgba(0,0,0,0.15);transition:transform 0.3s ease}
.stat-box:hover{transform:translateY(-2px);border-color:rgba(0,229,255,0.2)}
.stat-box .val{font-family:'Outfit',sans-serif;font-size:2rem;font-weight:800;color:var(--accent-color);background:var(--accent);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.stat-box .lbl{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:1.2px;margin-top:4px;font-weight:600}
.const-card{
  background:linear-gradient(145deg, rgba(18,22,38,0.85) 0%, rgba(10,12,24,0.85) 100%);
  border:1px solid rgba(108,53,255,0.2);box-shadow:0 0 30px rgba(108,53,255,0.08);
  padding:32px;border-radius:16px;margin-top:12px;
}
.const-title{font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;margin-bottom:20px;background:var(--accent);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.const-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px}
.const-item{background:rgba(255,255,255,0.01);border:1px solid var(--border);padding:20px;border-radius:12px;text-align:left;transition:all 0.3s ease}
.const-item:hover{transform:translateY(-2px);border-color:var(--accent2);background:rgba(255,255,255,0.02)}
.const-item h4{font-family:'Outfit',sans-serif;font-size:1rem;font-weight:700;color:var(--accent2);margin-bottom:8px}
.const-item p{font-size:0.8rem;color:var(--muted);line-height:1.5}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>Pravah Bhiv <span>&mdash; Ecosystem Observability</span></h1>
    <div style="font-size:.72rem;color:var(--muted);margin-top:4px;font-weight:500;letter-spacing:0.5px">Ecosystem Infrastructure Visibility &middot; Observe, Don't Own</div>
  </div>
  <div class="meta">
    <div id="clock"></div>
  </div>
</div>

<div class="container">
  <div class="stat-row" id="stats">
    <div class="stat-box"><div class="val" id="s-total">--</div><div class="lbl">Services Tracked</div></div>
    <div class="stat-box"><div class="val" id="s-healthy">--</div><div class="lbl">Healthy</div></div>
    <div class="stat-box"><div class="val" id="s-polls">--</div><div class="lbl">Poll Cycles</div></div>
    <div class="stat-box"><div class="val" id="s-events">--</div><div class="lbl">Events Captured</div></div>
  </div>

  <div class="tabs">
    <button class="tab-btn active" id="tab-btn-services" onclick="switchTab('services')">Services Health</button>
    <button class="tab-btn" id="tab-btn-graph" onclick="switchTab('graph')">Ecosystem Lineage Graph</button>
    <button class="tab-btn" id="tab-btn-lineage" onclick="switchTab('lineage')">Evidence Registry Logs</button>
    <button class="tab-btn" id="tab-btn-constitution" onclick="switchTab('constitution')">Constitutional Boundaries</button>
  </div>

  <!-- Services Tab -->
  <div id="tab-services" class="tab-content active">
    <div class="grid" id="service-cards"></div>
    <div class="events-card">
      <h3>Recent Observation Events <span id="event-count">--</span></h3>
      <div class="events-table-wrapper">
        <table class="events-table">
          <thead><tr><th>Time</th><th>Service</th><th>Status</th><th>Latency</th><th>Detail</th></tr></thead>
          <tbody id="events-body"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Graph Tab -->
  <div id="tab-graph" class="tab-content">
    <div class="events-card" style="margin-bottom: 24px;">
      <h3>Dynamic Ecosystem Dependency Visualization</h3>
      <div style="margin: 16px 0;">
        <svg width="100%" height="240" viewBox="0 0 1000 240" style="background:rgba(0,0,0,0.25); border-radius:12px; border:1px solid var(--border)">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#7e8b9f" />
            </marker>
            <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#00e676" />
            </marker>
            <marker id="arrow-yellow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#ffea00" />
            </marker>
          </defs>
          
          <!-- Connections -->
          <line x1="120" y1="120" x2="240" y2="120" stroke="#7e8b9f" stroke-width="2" marker-end="url(#arrow)" id="link-intent-runner" />
          <line x1="380" y1="120" x2="480" y2="120" stroke="#7e8b9f" stroke-width="2" marker-end="url(#arrow)" id="link-runner-plane" />
          <line x1="620" y1="120" x2="720" y2="120" stroke="#7e8b9f" stroke-width="2" marker-end="url(#arrow)" id="link-plane-registry" />
          <line x1="860" y1="120" x2="930" y2="120" stroke="#00e676" stroke-width="2" marker-end="url(#arrow-green)" id="link-registry-verification" />
          
          <!-- Nodes -->
          <circle cx="70" cy="120" r="35" fill="rgba(108,53,255,0.15)" stroke="#6c35ff" stroke-width="2" />
          <text x="70" y="124" fill="#f0f4fc" font-size="11" font-weight="600" text-anchor="middle" font-family="'Outfit'">Intent</text>
          
          <rect x="240" y="85" width="140" height="70" rx="12" fill="rgba(18,22,38,0.85)" stroke="#7e8b9f" stroke-width="2" id="node-runner" />
          <text x="310" y="115" fill="#f0f4fc" font-size="11" font-weight="700" text-anchor="middle" font-family="'Outfit'">Prompt Runner</text>
          <text x="310" y="136" fill="#7e8b9f" font-size="10" text-anchor="middle" id="lbl-runner" font-family="monospace">OFFLINE</text>
          
          <rect x="480" y="85" width="140" height="70" rx="12" fill="rgba(18,22,38,0.85)" stroke="#7e8b9f" stroke-width="2" id="node-plane" />
          <text x="550" y="115" fill="#f0f4fc" font-size="11" font-weight="700" text-anchor="middle" font-family="'Outfit'">Pravah Engine</text>
          <text x="550" y="136" fill="#7e8b9f" font-size="10" text-anchor="middle" id="lbl-plane" font-family="monospace">OFFLINE</text>
          
          <rect x="720" y="85" width="140" height="70" rx="12" fill="rgba(18,22,38,0.85)" stroke="#7e8b9f" stroke-width="2" id="node-registry" />
          <text x="790" y="115" fill="#f0f4fc" font-size="11" font-weight="700" text-anchor="middle" font-family="'Outfit'">Evidence Reg</text>
          <text x="790" y="136" fill="#7e8b9f" font-size="10" text-anchor="middle" id="lbl-registry" font-family="monospace">OFFLINE</text>
          
          <circle cx="955" cy="120" r="25" fill="rgba(0,230,118,0.1)" stroke="#00e676" stroke-width="2" />
          <text x="955" y="124" fill="#00e676" font-size="9" font-weight="800" text-anchor="middle" font-family="'Outfit'">VERIFIED</text>
        </svg>
      </div>
      <p style="font-size:0.8rem;color:var(--muted);line-height:1.5">This diagram displays the real-time runtime communication logic. If the services are running and verified healthy, their connection lineage glows green, indicating continuous E2E trace continuity.</p>
    </div>
  </div>

  <!-- Lineage Tab -->
  <div id="tab-lineage" class="tab-content">
    <div class="events-card">
      <h3>Active Shakti Evidence Bundles</h3>
      <div class="events-table-wrapper">
        <table class="events-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Bundle ID</th>
              <th>Trace ID</th>
              <th>Execution ID</th>
              <th>Type</th>
              <th>Authority Chain</th>
              <th>Evidence Data</th>
            </tr>
          </thead>
          <tbody id="lineage-body"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Constitution Tab -->
  <div id="tab-constitution" class="tab-content">
    <div class="const-card">
      <h3 class="const-title">Ecosystem Governance & Bounded Authority</h3>
      <p style="font-size:0.9rem;color:var(--muted);margin-bottom:24px;line-height:1.6">Pravah functions strictly as an ecosystem visibility layer. To satisfy TANTRA constitutional safeguards, observability metrics must never assume governance authority or interfere with core service processing.</p>
      <div class="const-grid">
        <div class="const-item">
          <h4>Observability &ne; Authority</h4>
          <p>Ecosystem metrics gather trace continuity data passively. Pravah has zero execution right or veto power over product runtimes.</p>
        </div>
        <div class="const-item">
          <h4>Replay &ne; Truth</h4>
          <p>Replay simulations prove state equivalence and trace recovery correctness, but do not dictate system operational state.</p>
        </div>
        <div class="const-item">
          <h4>Telemetry &ne; Governance</h4>
          <p>Governance belongs strictly to human operators or the sovereign GC. Pravah telemetry reports metrics, it does not enforce law.</p>
        </div>
        <div class="const-item">
          <h4>Visibility &ne; Execution</h4>
          <p>Visibility grants full trace audit chains, but holds no permission to alter runtimes, configuration, or active data states.</p>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="footer">Pravah Bhiv Observer v2.0.0 &middot; Auto-refreshes every 5 s &middot; Secure & Independent</div>

<script>
function badgeHtml(status){return `<span class="badge ${status}">${status}</span>`}
function pulseHtml(status){return `<span class="pulse ${status}"></span>`}

function switchTab(tabId){
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
  
  document.getElementById(`tab-btn-${tabId}`).classList.add('active');
  document.getElementById(`tab-${tabId}`).classList.add('active');
}

async function refresh(){
  try{
    const [statusRes,eventsRes,lineageRes]=await Promise.all([
      fetch('/api/status'),
      fetch('/api/events?limit=30'),
      fetch('/api/lineage')
    ]);
    const status=await statusRes.json();
    const evData=await eventsRes.json();
    const linData=await lineageRes.json();

    // stats
    const svcs=Object.keys(status.services);
    document.getElementById('s-total').textContent=svcs.length;
    document.getElementById('s-healthy').textContent=svcs.filter(k=>status.services[k].status==='healthy').length;
    document.getElementById('s-polls').textContent=status.poll_count;
    document.getElementById('s-events').textContent=evData.total;
    document.getElementById('event-count').textContent=`${evData.total} items`;

    // service cards
    let cards='';
    for(const[name,info]of Object.entries(status.services)){
      cards+=`<div class="card">
        <h3>Observed Service ${pulseHtml(info.status)}</h3>
        <div class="svc-name">${name}</div>
        <div class="svc-url">${info.url}</div>
        <div class="svc-latency">${info.latency_ms}<small> ms</small></div>
        ${badgeHtml(info.status)}
        <div style="margin-top:14px;font-size:.72rem;color:var(--muted);font-weight:500">Last checked: ${new Date(info.last_checked+'Z').toLocaleTimeString()}</div>
      </div>`;
    }
    document.getElementById('service-cards').innerHTML=cards;


    // events table
    let rows='';
    for(const e of evData.events){
      rows+=`<tr>
        <td>${new Date(e.ts+'Z').toLocaleTimeString()}</td>
        <td style="font-weight:600">${e.service}</td>
        <td>${badgeHtml(e.status)}</td>
        <td style="font-family:monospace;font-weight:500">${e.latency_ms} ms</td>
        <td class="detail-cell" title="${(e.detail||'').replace(/"/g,'&quot;')}">${e.detail||'-'}</td>
      </tr>`;
    }
    document.getElementById('events-body').innerHTML=rows;

    // dependency graph updates
    const runner = status.services['prompt-runner01'];
    const plane = status.services['control-plane'];
    const sarathi = status.services['bhiv-sarathi'];
    
    // runner node color & text
    if (runner) {
      const color = runner.status === 'healthy' ? '#00e676' : (runner.status === 'degraded' ? '#ffea00' : '#ff1744');
      const arrowColor = runner.status === 'healthy' ? 'url(#arrow-green)' : (runner.status === 'degraded' ? 'url(#arrow-yellow)' : 'url(#arrow)');
      const linkStroke = runner.status === 'healthy' ? '#00e676' : (runner.status === 'degraded' ? '#ffea00' : '#7e8b9f');
      document.getElementById('node-runner').setAttribute('stroke', color);
      document.getElementById('lbl-runner').textContent = runner.status.toUpperCase();
      document.getElementById('lbl-runner').setAttribute('fill', color);
      document.getElementById('link-intent-runner').setAttribute('stroke', linkStroke);
      document.getElementById('link-intent-runner').setAttribute('marker-end', arrowColor);
    }
    
    // control plane node color & text
    if (plane) {
      const color = plane.status === 'healthy' ? '#00e676' : (plane.status === 'degraded' ? '#ffea00' : '#ff1744');
      const arrowColor = plane.status === 'healthy' ? 'url(#arrow-green)' : (plane.status === 'degraded' ? 'url(#arrow-yellow)' : 'url(#arrow)');
      const linkStroke = plane.status === 'healthy' ? '#00e676' : (plane.status === 'degraded' ? '#ffea00' : '#7e8b9f');
      document.getElementById('node-plane').setAttribute('stroke', color);
      document.getElementById('lbl-plane').textContent = plane.status.toUpperCase();
      document.getElementById('lbl-plane').setAttribute('fill', color);
      document.getElementById('link-runner-plane').setAttribute('stroke', linkStroke);
      document.getElementById('link-runner-plane').setAttribute('marker-end', arrowColor);
    }
    
    // evidence registry updates (if control plane is up and evidence endpoint responds)
    if (plane && plane.status === 'healthy') {
      document.getElementById('node-registry').setAttribute('stroke', '#00e676');
      document.getElementById('lbl-registry').textContent = 'CONNECTED';
      document.getElementById('lbl-registry').setAttribute('fill', '#00e676');
      document.getElementById('link-plane-registry').setAttribute('stroke', '#00e676');
      document.getElementById('link-plane-registry').setAttribute('marker-end', 'url(#arrow-green)');
    } else {
      document.getElementById('node-registry').setAttribute('stroke', '#7e8b9f');
      document.getElementById('lbl-registry').textContent = 'OFFLINE';
      document.getElementById('lbl-registry').setAttribute('fill', '#7e8b9f');
      document.getElementById('link-plane-registry').setAttribute('stroke', '#7e8b9f');
      document.getElementById('link-plane-registry').setAttribute('marker-end', 'url(#arrow)');
    }

    // lineages logs table
    let linRows = '';
    for(const l of linData.lineages){
      const chainStr = (l.authority_chain || []).join(' &rarr; ');
      const t = l.produced_at ? new Date(l.produced_at).toLocaleTimeString() : '--';
      const rawEvidence = JSON.stringify(l.evidence || {}).replace(/"/g, '&quot;');
      linRows += `<tr>
        <td>${t}</td>
        <td style="font-family:monospace;font-weight:600">${l.bundle_id || '--'}</td>
        <td style="font-family:monospace">${l.trace_id || '--'}</td>
        <td style="font-family:monospace;color:var(--muted)">${l.execution_id || '--'}</td>
        <td><span class="badge info">${l.decision_type || '--'}</span></td>
        <td style="font-size:0.75rem;font-weight:600;color:var(--accent2)">${chainStr}</td>
        <td class="detail-cell" title="${rawEvidence}">${JSON.stringify(l.evidence || {})}</td>
      </tr>`;
    }
    document.getElementById('lineage-body').innerHTML = linRows || '<tr><td colspan="7" style="text-align:center;color:var(--muted)">No evidence bundles registered yet</td></tr>';

  }catch(err){console.error('refresh failed',err)}
}

function tick(){document.getElementById('clock').textContent=new Date().toLocaleTimeString()}
setInterval(refresh,5000);
setInterval(tick,1000);
tick();refresh();
</script>
</body>
</html>"""





# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    print(f"[Pravah Observer] Polling services every 10s")
    print(f"[Pravah Observer] Gurukul Backend target: {GURUKUL_API_URL}")
    print(f"[Pravah Observer] INFIVERSE HR Platform target: {HR_API_URL}  <- NEW")
    print(f"[Pravah Observer] CRM API target: {CRM_API_URL}")
    print(f"[Pravah Observer] Main API target: {MAIN_API_URL}")
    print(f"[Pravah Observer] Control Plane target: {CONTROL_PLANE_URL}")
    print(f"[Pravah Observer] Dashboard: http://localhost:{OBSERVER_PORT}")

    uvicorn.run(app, host="0.0.0.0", port=OBSERVER_PORT, log_level="info")


if __name__ == "__main__":
    main()
