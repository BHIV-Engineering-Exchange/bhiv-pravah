# The TANTRA Pipeline Architecture

In the architecture of this project, **KESHAV** acts as the very first analytical step in a much larger, strictly controlled pipeline called **TANTRA**. 

The TANTRA workflow is essentially a series of checkpoints (or "layers"). When you send the input to the `/analyze` endpoint, it goes through this exact lifecycle in the background:

## The 6 Layers of the Pipeline

### 1. SETU (The Input Bridge)
You send your JSON payload to the API. SETU accepts it and validates that it contains a `trace_id` (this trace ID acts like a tracking number that must never change).

### 2. KESHAV (The Analyzer Layer)
KESHAV looks at the broken tasks, figures out the root cause, and generates the recommended fix (e.g., finding out that Task A caused Task B to fail).

### 3. RAJYA (The Decision Layer)
KESHAV hands its output directly to RAJYA. RAJYA's only job is to act as a strict checkpoint. It performs absolutely *zero* data transformations and verifies that KESHAV did not illegally modify the `trace_id`. 

### 4. Sarathi (The Enforcement Layer)
RAJYA passes the data to Sarathi. Sarathi looks at KESHAV's recommendation (e.g., `UNBLOCK_DEPENDENCY`) and formally generates an "enforcement ticket" authorizing the system to take that action.

### 5. Core (The Execution Layer)
Core takes the authorization from Sarathi and actually "executes" the fix.

### 6. Bucket (The Truth Layer)
Once Core is done, Bucket takes the final results and saves them permanently in memory. Bucket is append-only, meaning once data is written, it can never be altered.

---

## Side-Channel: InsightFlow
While all of this is happening, a separate system called **InsightFlow** quietly watches KESHAV. It is a strictly read-only observability layer that generates metrics and event logs for dashboards (like Grafana or Prometheus) without ever interfering with the main pipeline. 

## Why is it built this way?
This workflow ensures **fail-closed trace continuity**. The `trace_id` from your input is tracked through every single layer. If any layer drops the trace ID or attempts to mutate data illegally, the entire pipeline immediately halts and throws an error to prevent corrupted data from reaching the **Bucket**.
