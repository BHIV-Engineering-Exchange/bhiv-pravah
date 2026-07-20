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
BUCKET_API_URL = os.getenv("PRAVAH_BUCKET_API", "http://localhost:8000")


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
    """Background thread that continuously polls observed services."""
    while True:
        services = {
            "crm-api": {
                "url": CRM_API_URL,
                "health_url": f"{CRM_API_URL}/health"
            },
            "main-api": {
                "url": MAIN_API_URL,
                "health_url": f"{MAIN_API_URL}/health"
            },
            "control-plane": {
                "url": CONTROL_PLANE_URL,
                "health_url": f"{CONTROL_PLANE_URL}/api/health"
            },
            "bhiv-bucket": {
                "url": BUCKET_API_URL,
                "health_url": f"{BUCKET_API_URL}/health"
            }
        }
        for svc_name, svc_cfg in services.items():
            _probe_service(svc_name, svc_cfg["health_url"], svc_cfg["url"])
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
<title>Pravah Bhiv - Observer Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#070a13;--surface:#0e1322;--card:rgba(20,27,45,0.7);--border:rgba(255,255,255,0.06);
  --text:#f0f4fc;--muted:#8f9cb3;--accent:linear-gradient(135deg, #7c4dff 0%, #18ffff 100%);
  --accent-color:#7c4dff;--accent2:#00e5ff;
  --green:#00e676;--red:#ff1744;--yellow:#ffea00;--blue:#2979ff;
  --glow-green:rgba(0,230,118,0.15);--glow-red:rgba(255,23,68,0.15);--glow-yellow:rgba(255,234,0,0.15);
}
body{font-family:'Inter',sans-serif;background-color:var(--bg);background-image:radial-gradient(circle at 10% 20%, rgba(124,77,255,0.05) 0%, transparent 40%), radial-gradient(circle at 90% 80%, rgba(24,255,255,0.05) 0%, transparent 40%);color:var(--text);min-height:100vh;overflow-x:hidden}
.header{
  background:rgba(14,19,34,0.8);
  backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
  border-bottom:1px solid var(--border);padding:24px 40px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:100;
}
.header h1{font-family:'Outfit',sans-serif;font-size:1.6rem;font-weight:800;letter-spacing:-.8px;background:var(--accent);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header h1 span{font-weight:400;color:var(--muted);-webkit-text-fill-color:var(--muted)}
.header .meta{font-size:.85rem;color:var(--muted);font-weight:500;display:flex;align-items:center;gap:12px}
#clock{background:rgba(255,255,255,0.03);padding:6px 14px;border-radius:30px;border:1px solid var(--border);color:var(--text);font-family:monospace;letter-spacing:0.5px}
.badge{display:inline-block;padding:4px 12px;border-radius:30px;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;transition:all 0.3s ease}
.badge.healthy{background:rgba(0,230,118,.12);color:var(--green);border:1px solid rgba(0,230,118,0.2);box-shadow:0 0 10px var(--glow-green)}
.badge.unreachable,.badge.error{background:rgba(255,23,.12);color:var(--red);border:1px solid rgba(255,23,68,0.2);box-shadow:0 0 10px var(--glow-red)}
.badge.degraded,.badge.timeout{background:rgba(255,234,0,.1);color:var(--yellow);border:1px solid rgba(255,234,0,0.2);box-shadow:0 0 10px var(--glow-yellow)}
.badge.info{background:rgba(124,77,255,.12);color:var(--accent-color);border:1px solid rgba(124,77,255,0.2)}
.container{max-width:1400px;margin:0 auto;padding:40px 24px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:24px;margin-bottom:40px}
.card{background:var(--card);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid var(--border);border-radius:16px;padding:28px;transition:all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);box-shadow:0 8px 32px 0 rgba(0,0,0,0.2)}
.card:hover{transform:translateY(-5px);border-color:rgba(124,77,255,0.3);box-shadow:0 12px 40px rgba(124,77,255,0.12)}
.card h3{font-family:'Outfit',sans-serif;font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:18px;display:flex;align-items:center;justify-content:space-between}
.svc-name{font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:700;margin-bottom:8px;color:#ffffff;letter-spacing:-0.3px}
.svc-url{font-size:.75rem;color:var(--muted);word-break:break-all;font-family:monospace;background:rgba(0,0,0,0.2);padding:6px 10px;border-radius:6px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.02)}
.svc-latency{font-family:'Outfit',sans-serif;font-size:2rem;font-weight:800;color:var(--accent2);margin:16px 0 10px;display:flex;align-items:baseline;gap:4px}
.svc-latency small{font-size:.85rem;color:var(--muted);font-weight:400;font-family:'Inter',sans-serif}
.events-card{background:var(--card);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid var(--border);border-radius:16px;padding:32px;box-shadow:0 8px 32px 0 rgba(0,0,0,0.2)}
.events-card h3{font-family:'Outfit',sans-serif;font-size:1.1rem;font-weight:700;margin-bottom:24px;color:#ffffff;letter-spacing:-0.3px;display:flex;align-items:center;justify-content:space-between}
.events-card h3 span{font-size:0.75rem;color:var(--muted);font-weight:400;background:rgba(255,255,255,0.03);padding:4px 10px;border-radius:20px;border:1px solid var(--border)}
.events-table-wrapper{overflow-x:auto}
.events-table{width:100%;border-collapse:collapse;text-align:left}
.events-table th,.events-table td{padding:16px 20px;border-bottom:1px solid var(--border);font-size:.85rem}
.events-table th{color:var(--muted);font-weight:600;text-transform:uppercase;font-size:.75rem;letter-spacing:1px;background:rgba(255,255,255,0.01)}
.events-table td{color:var(--text)}
.events-table tr{transition:background-color 0.2s ease}
.events-table tr:hover{background:rgba(124,77,255,0.03)}
.detail-cell{max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted);font-family:monospace;font-size:0.8rem}
.pulse{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:8px;position:relative;vertical-align:middle}
.pulse.healthy{background:var(--green);box-shadow:0 0 10px var(--green)}
.pulse.unreachable,.pulse.error{background:var(--red);box-shadow:0 0 10px var(--red)}
.pulse.degraded,.pulse.timeout{background:var(--yellow);box-shadow:0 0 10px var(--yellow)}
.pulse::after{content:'';width:100%;height:100%;border-radius:50%;position:absolute;top:0;left:0;animation:pulse-ring 2.5s infinite;opacity:0.4}
.pulse.healthy::after{border:1px solid var(--green)}
.pulse.unreachable::after,.pulse.error::after{border:1px solid var(--red)}
.pulse.degraded::after,.pulse.timeout::after{border:1px solid var(--yellow)}
@keyframes pulse-ring{0%{transform:scale(1);opacity:0.4}50%{transform:scale(2.2);opacity:0}100%{transform:scale(1);opacity:0}}
.footer{text-align:center;padding:32px;color:var(--muted);font-size:.8rem;border-top:1px solid var(--border);margin-top:60px;letter-spacing:0.5px}
.stat-row{display:flex;gap:20px;margin-bottom:40px;flex-wrap:wrap}
.stat-box{flex:1;min-width:200px;background:var(--card);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid var(--border);border-radius:16px;padding:24px;text-align:center;box-shadow:0 8px 32px 0 rgba(0,0,0,0.15);transition:transform 0.3s ease}
.stat-box:hover{transform:translateY(-2px);border-color:rgba(24,255,255,0.2)}
.stat-box .val{font-family:'Outfit',sans-serif;font-size:2.2rem;font-weight:800;color:var(--accent-color);background:var(--accent);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.stat-box .lbl{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-top:6px;font-weight:600}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>Pravah Bhiv <span>&mdash; Observer Dashboard</span></h1>
    <div style="font-size:.78rem;color:var(--muted);margin-top:4px;font-weight:500;letter-spacing:0.5px">Execution Visibility Layer &middot; Observe, Don't Own</div>
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

<div class="footer">Pravah Bhiv Observer v1.1.0 &middot; Auto-refreshes every 5 s &middot; Secure & Independent</div>

<script>
function badgeHtml(status){return `<span class="badge ${status}">${status}</span>`}
function pulseHtml(status){return `<span class="pulse ${status}"></span>`}

async function refresh(){
  try{
    const [statusRes,eventsRes]=await Promise.all([fetch('/api/status'),fetch('/api/events?limit=30')]);
    const status=await statusRes.json();
    const evData=await eventsRes.json();

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
    # Start background poller thread
    poller = threading.Thread(target=_poll_loop, args=(10.0,), daemon=True)
    poller.start()
    print(f"[Pravah Observer] Polling services every 10s")
    print(f"[Pravah Observer] CRM API target: {CRM_API_URL}")
    print(f"[Pravah Observer] Main API target: {MAIN_API_URL}")
    print(f"[Pravah Observer] Control Plane target: {CONTROL_PLANE_URL}")
    print(f"[Pravah Observer] Dashboard: http://localhost:{OBSERVER_PORT}")

    uvicorn.run(app, host="0.0.0.0", port=OBSERVER_PORT, log_level="info")


if __name__ == "__main__":
    main()
