# Workflow Executor  
**Production Deterministic Real-World Execution Engine**

Workflow Executor is the **single, authoritative execution layer** for the BHIV ecosystem.  
It converts approved assistant workflows into **deterministic, traceable real-world actions**.

This service is **execution-only**:
- No UI
- No reasoning
- No emotional logic

---

## 🎯 Purpose

- Execute workflows **only when explicitly approved**
- Enforce deterministic, single-path execution
- Guarantee explicit success / failure
- Preserve traceability across all products

---

## 🌐 Live Deployment

**Base URL**  
https://workflow-executor-mp4x.onrender.com  

**API Docs**  
https://workflow-executor-mp4x.onrender.com/docs  

**Primary Endpoint**
POST /api/workflow/execute

---

## 🔐 Execution Gate (Hard Rule)

Execution happens **only** when:
```json
"decision": "workflow"
```
All other decisions are safely skipped and logged.

## 📦 Request Contract
```json
{
  "trace_id": "unique-id",
  "decision": "workflow",
  "data": {
    "workflow_type": "workflow",
    "payload": {
      "action_type": "task"
    }
  }
}
```

## 🔌 Supported Execution Adapters
| action_type | Capability |
|-------------|------------|
| ai | External AI execution |
| whatsapp | Message delivery |
| email | Email dispatch |
| task | Task creation |
| reminder | Reminder scheduling |

Unsupported actions fail explicitly.

## ⚙️ Execution Guarantees

- One request → one execution path

- Adapter chosen only by action_type

- No retries, no hidden fallbacks

- No silent failures

- Stable response contract

- Full trace_id propagation

## 🧪 Verified Proof

- AI execution from AI Assistant

- Safe failure handling

- WhatsApp execution from Gurukul

- Task creation workflow

- Telemetry emitted to InsightFlow

- Cross-product trace chain verified

## 🚀 Run Locally

**Method 1: Direct Python (Recommended)**
```bash
pip install -r requirements.txt
python main.py
```

**Method 2: Uvicorn with explicit port**
```bash
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

**Method 3: Windows Quick Start**
```bash
start_correct_port.bat
```

**IMPORTANT**: Always use port 8003. Do NOT use `uvicorn main:app --reload` without `--port 8003`

**Docs**: http://127.0.0.1:8003/docs  
**Health**: http://127.0.0.1:8003/healthz  
**Port**: 8003 (CRITICAL: Karma uses 8000, Bucket uses 8001, Core uses 8002)

## ✅ Final Status

- Shared execution service live

- All products routed through executor

- Determinism preserved

- Governance boundaries enforced

- Production ready

**Workflow Executor is now the live, stable, deterministic execution authority.**