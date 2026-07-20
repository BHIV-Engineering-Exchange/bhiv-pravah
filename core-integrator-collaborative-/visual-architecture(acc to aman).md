# Visual Architecture (According to Aman)

Below is the visual architecture diagram representing the system workflow and integrations.

![Visual Architecture Diagram](https://drive.google.com/uc?export=view&id=1QLoJTxNfZ4nh8BKH41um30X8353NxNC8)

*If the image doesn't load directly, you can also view it here: [Google Drive Link](https://drive.google.com/file/d/1QLoJTxNfZ4nh8BKH41um30X8353NxNC8/view?usp=sharing)*

## Overview
Aman's visual architecture diagram represents the **canonical runtime pathway for the TANTRA ecosystem**. The system is structured as an asynchronous, trace-safe, and secure microservices network. It separates request orchestration, translation, design-time blueprinting, and policy validation from the actual execution engines. 

Key architectural patterns in this system include:
- **Strict Decoupled Configurations:** All microservices listen on independent ports (`8000`-`8008`) and resolve service locations dynamically via environment variables rather than hardcoded URLs.
- **Unified Trace Propagation:** A single `trace_id` and `workflow_id` are seeded at the entry point and must remain unchanged as they pass through every downstream component.
- **Contract-Based Validation:** Blueprints are compiled into immutable contracts that must satisfy deterministic, cryptographic, and security policies before triggering physical module runs.
- **Append-Only Telemetry & Archival:** The pipeline logs all states to `InsightFlow` telemetry and archives the entire execution lineage (A1 Instruction → A2 Blueprint → A3 Contract → A4 Execution) to the `BHIV Bucket`.

---

## Main Integration Flow

The runtime execution sequence proceeds step-by-step as follows:

### Step 1: Ingestion & Initial Tracing (Integration Bridge)
- **Port:** `8004`
- **Action:** The client sends a natural language prompt to `POST /pipeline/execute`. The bridge initializes a `trace_id` and `workflow_id` which are injected as HTTP headers (`X-Trace-Id` and `X-Workflow-Id`) on all subsequent calls.

### Step 2: Intent Translation (Prompt Runner)
- **Port:** `8003` (Deployed on Render)
- **Action:** The bridge passes the prompt to `POST /generate` on the Prompt Runner. The runner uses Groq API (requiring `GROQ_API_KEY`) to parse human intent into a structured instruction JSON (A1) containing defined parameters (`prompt`, `module`, `intent`, `topic`, `tasks`, `output_format`, `product_context`).

### Step 3: Blueprint Generation (Creator Core)
- **Port:** `8000`
- **Action:** The bridge forwards the instruction (A1) to `POST /creator-core/generate-blueprint` on Creator Core. It parses the intent and constructs a structured `BlueprintEnvelope` (A2) defining target products, scene options, light profiles, and asset specifications.

### Step 4: Central Routing (BHIV Core)
- **Port:** `8001`
- **Action:** The bridge forwards the blueprint (A2) to `POST /core` on BHIV Core. Recognizing it as a Creator Core instruction, the core delegates it to the [RoutingEngine](file:///c:/Core-integrator-collaborative/core-integrator-collaborative-/src/core/routing_engine.py) to initiate the TANTRA validation sub-flow.

### Step 5: Contract Translation (CET Service)
- **Port:** `8006`
- **Action:** The `RoutingEngine` sends a request to the CET (Constitutional Execution Translator) at `POST /contract/compile`. CET compiles the blueprint variables into a deterministic execution contract containing strict physics rules, gravity directions, and game constraints.

### Step 6: Policy Validation (Sarathi Service)
- **Port:** `8007`
- **Action:** The `RoutingEngine` sends the contract to Sarathi at `POST /authority/validate`. Sarathi acts as the policy checker, auditing the contract format, checking transaction signatures, validating unique nonces, and returning a boolean `allowed` decision.

### Step 7: Enforced Gate Execution (Gate Service)
- **Port:** `8008`
- **Action:** The `RoutingEngine` forwards the contract and authorization response to `POST /gate/evaluate` on the Execution Gate.
  - If authorized, the Gate routes the plan to the target engine.
  - For external integrations like **TTG/TTV**, the Gate strips prohibited metadata and formats the execution payload to match the `engineExecutionContract_v3` spec. It signs the request using `HMAC-SHA256` and posts it to the Node.js microservice (`http://localhost:3000/execute`).
  - The Gate returns the finalized execution result.

### Step 8: Lineage Archival (BHIV Bucket)
- **Port:** `8005`
- **Action:** The `RoutingEngine` records the full artifact chain (A1 Instruction → A2 Blueprint → A3 Contract → A4 Execution) to the append-only `BHIV Bucket` via `POST /bucket/store`. The trace index is updated to allow post-facto reconstruction and determinism checks via the Replay engine.

