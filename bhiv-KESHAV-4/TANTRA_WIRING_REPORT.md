# TANTRA Wiring Report
**Phase 3 — TANTRA Wiring Validation**

**Objective**: Verify actual runtime path for the `SETU/Input → KESHAV → RAJYA → Sarathi → Core → Bucket` pipeline, including InsightFlow observability.

## 1. SETU/Input → KESHAV
* **Input Contract**: Dictionary containing `trace_id`, `execution_id`, `tasks`, `constraint_results`, and `propagation_results`.
* **Output Contract**: Dictionary containing `trace_id`, `execution_id`, `root_cause`, `resolution_signal`, `impact_score`, `severity`, and `timestamp`.
* **File Location**: `analyzer/analyze_blockage.py`
* **Execution Path**: `analyze_and_recommend(input_data)`
* **Trace Continuity Proof**: The `trace_id` is extracted from the input dictionary and passed completely unchanged to `structure_output()` before being returned. It is never generated or modified by KESHAV.

## 2. KESHAV → RAJYA
* **Input Contract**: The exact dictionary output from KESHAV (`keshav_output`) and `trace_id`.
* **Output Contract**: The exact identical dictionary (`rajya_output`). RAJYA performs zero transformations.
* **File Location**: `tantra/rajya.py`
* **Execution Path**: `rajya.consume(keshav_output, trace_id)`
* **Trace Continuity Proof**: RAJYA enforces continuity via `if keshav_output["trace_id"] != expected_trace_id: raise ValueError(...)`. The output matches the input byte-for-byte.

## 3. RAJYA → Sarathi
* **Input Contract**: The `rajya_output` dictionary.
* **Output Contract**: An enforcement dictionary containing `trace_id`, `enforced` (bool), `resolution_signal`, and `action`.
* **File Location**: `tantra/sarathi.py`
* **Execution Path**: `sarathi.enforce(rajya_output)`
* **Trace Continuity Proof**: Extracts `trace_id` from `rajya_output` (`rajya_output.get("trace_id")`) and asserts its presence. Places the exact `trace_id` directly into the returned `sarathi_output`.

## 4. Sarathi → Core
* **Input Contract**: The `sarathi_output` enforcement dictionary.
* **Output Contract**: An execution dictionary containing `trace_id`, `executed` (bool), and `action`.
* **File Location**: `tantra/core.py`
* **Execution Path**: `core.execute(sarathi_output)`
* **Trace Continuity Proof**: Extracts `trace_id` from `sarathi_output` (`sarathi_output.get("trace_id")`) and asserts its presence. Places the exact `trace_id` directly into the returned `core_output`.

## 5. Core → Bucket
* **Input Contract**: The `core_output` dictionary and the original `keshav_output` dictionary.
* **Output Contract**: No data returned. Data is persisted to an in-memory dictionary acting as the persistent truth store.
* **File Location**: `tantra/bucket.py`
* **Execution Path**: `bucket.write(core_output, keshav_output)`
* **Trace Continuity Proof**: Extracts `trace_id` from `core_output`. Uses `trace_id` as the primary key to store the outputs in the thread-safe `_store` dictionary. Will fail-closed if `trace_id` is missing.

## 6. KESHAV → InsightFlow
* **Input Contract**: The original `keshav_output` dictionary.
* **Output Contract**: No data returned. Structured `EXECUTION` or `FAILURE` events are emitted to an in-memory event log.
* **File Location**: `tantra/insightflow.py`
* **Execution Path**: `insightflow.emit(keshav_output)`
* **Trace Continuity Proof**: InsightFlow reads `trace_id` directly from `keshav_output` and logs it inside the `event` dictionary. The data flow is strictly read-only and does not mutate the `keshav_output` dictionary for any downstream hops.

## Summary
The full execution path is strictly orchestrated by `tantra/pipeline.py::run_tantra_pipeline()`.
**Actual Runtime Path Verified.** Trace continuity is unbroken, with all stages explicitly raising fail-closed `ValueError` if `trace_id` is missing or mismatched. There is no transformation of the core signal outside its intended boundaries.
