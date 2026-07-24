# Runtime Attachment Audit

**Phase 2 — Runtime Attachment Validation**
This document maps the live execution flow of the TANTRA pipeline, verifying the attachment and contract boundaries across all ecosystem layers.

## 1. Signal Layer
* **Owner**: Ecosystem
* **Implementation**: External dictionary payload containing `trace_id` and initial state.
* **Runtime Location**: `tantra/pipeline.py` (entry point: `input_data` to `run_tantra_pipeline`)
* **Attachment Mode**: Synchronous Function Invocation
* **Contract Boundary**: Input dictionary must provide at minimum a valid `trace_id`.
* **Trace Boundary**: `trace_id` is passed unmodified into the pipeline.

## 2. Intelligence Layer
* **Owner**: Rajaryan Verma (KESHAV)
* **Implementation**: `analyzer.analyze_blockage.analyze_and_recommend`
* **Runtime Location**: `tantra/pipeline.py` (lines 37-42)
* **Attachment Mode**: Direct Local Invocation
* **Contract Boundary**: Consumes Signal input, yields `keshav_output` containing deterministic root cause analysis.
* **Trace Boundary**: The `trace_id` is maintained byte-for-byte; no generation or modification occurs inside this boundary.

## 3. Decision Layer
* **Owner**: RAJYA Owner
* **Implementation**: `tantra.rajya.consume(keshav_output, trace_id)`
* **Runtime Location**: `tantra/pipeline.py` (lines 44-48)
* **Attachment Mode**: Synchronous Invocation
* **Contract Boundary**: Consumes exact `keshav_output` dictionary. Fails-closed on violation. Yields `rajya_output`.
* **Trace Boundary**: Hard validation on `trace_id` matching exactly with KESHAV's output.

## 4. Contract Layer
* **Owner**: Ashmit (Ecosystem Integration Validation)
* **Implementation**: TANTRA Pipeline Orchestrator (`tantra/pipeline.py`)
* **Runtime Location**: `tantra/pipeline.py`
* **Attachment Mode**: Orchestration/Sequence Control
* **Contract Boundary**: Prevents cross-contamination by passing specific outputs sequentially, preventing skip-level bypasses.
* **Trace Boundary**: Fail-closed mechanism; any exception or invalid state terminates the pipeline and returns `status=FAIL`.

## 5. Enforcement Layer
* **Owner**: Sarathi Owner
* **Implementation**: `tantra.sarathi.enforce(rajya_output)`
* **Runtime Location**: `tantra/pipeline.py` (lines 50-54)
* **Attachment Mode**: Synchronous Invocation
* **Contract Boundary**: Consumes `rajya_output`. Validates logic before returning `sarathi_output` containing enforcement directives.
* **Trace Boundary**: Extracts and embeds the exact `trace_id` into its enforcement output.

## 6. Execution Layer
* **Owner**: Core Owner
* **Implementation**: `tantra.core.execute(sarathi_output)`
* **Runtime Location**: `tantra/pipeline.py` (lines 56-60)
* **Attachment Mode**: Synchronous Invocation
* **Contract Boundary**: Consumes `sarathi_output` to perform execution. Returns `core_output` reflecting physical execution state.
* **Trace Boundary**: Asserts the exact `trace_id` matches the input enforcement data.

## 7. Truth Layer
* **Owner**: Bucket Owner
* **Implementation**: `tantra.bucket.write(core_output, keshav_output)`
* **Runtime Location**: `tantra/pipeline.py` (lines 62-63)
* **Attachment Mode**: Write-On-Success (Terminal Node)
* **Contract Boundary**: Consumes both execution results and original intelligence output for state anchoring.
* **Trace Boundary**: Uses the unmodified `trace_id` as the primary key for the in-memory persistence store.

## 8. Observability Layer
* **Owner**: InsightFlow Owner
* **Implementation**: `tantra.insightflow.emit(keshav_output)`
* **Runtime Location**: `tantra/pipeline.py` (line 39)
* **Attachment Mode**: Read-Only Emission (Asynchronous semantics)
* **Contract Boundary**: Consumes `keshav_output` immediately after generation. Zero mutation allowed.
* **Trace Boundary**: Directly references `trace_id` for its external logging structure.

## Summary: Convergence Condition Met
* **Condition:** No undocumented runtime participant remains.
* **Validation:** All components from Signal -> Truth are documented, strictly bound by the `trace_id` propagation, and fully identified by ownership and boundary controls.
