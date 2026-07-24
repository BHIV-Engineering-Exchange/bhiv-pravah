"""
TANTRA Pipeline — Full chain execution

SETU/Input → KESHAV → RAJYA → Sarathi → Core → Bucket

Rules:
- trace_id must be identical across all layers
- Fail-closed: any layer failure stops the chain; no write to Bucket
- InsightFlow is read-only observability; never mutates output
- Zero transformation between layers
"""

from analyzer.analyze_blockage import analyze_and_recommend

from . import bucket, core, insightflow, rajya, sarathi


def run_tantra_pipeline(input_data: dict) -> dict:
    """
    Execute the full TANTRA chain for one input.

    Returns:
        {
            "trace_id":       str,
            "status":         "OK" | "FAIL",
            "keshav_output":  dict,
            "rajya_output":   dict | None,
            "sarathi_output": dict | None,
            "core_output":    dict | None,
            "error":          str | None,
        }

    On any failure: status=FAIL, error set, no Bucket write.
    """
    trace_id = input_data.get("trace_id", "") if isinstance(input_data, dict) else ""

    # ── KESHAV ────────────────────────────────────────────────────────────────
    keshav_output = analyze_and_recommend(input_data)
    insightflow.emit(keshav_output)

    if keshav_output.get("status") == "FAIL":
        return _fail(trace_id, keshav_output, "KESHAV returned FAIL")

    # ── RAJYA ─────────────────────────────────────────────────────────────────
    try:
        rajya_output = rajya.consume(keshav_output, trace_id)
    except Exception as exc:
        return _fail(trace_id, keshav_output, str(exc))

    # ── Sarathi ───────────────────────────────────────────────────────────────
    try:
        sarathi_output = sarathi.enforce(rajya_output)
    except Exception as exc:
        return _fail(trace_id, keshav_output, str(exc))

    # ── Core ──────────────────────────────────────────────────────────────────
    try:
        core_output = core.execute(sarathi_output)
    except Exception as exc:
        return _fail(trace_id, keshav_output, str(exc))

    # ── Bucket ────────────────────────────────────────────────────────────────
    bucket.write(core_output, keshav_output)

    return {
        "trace_id": trace_id,
        "status": "OK",
        "keshav_output": keshav_output,
        "rajya_output": rajya_output,
        "sarathi_output": sarathi_output,
        "core_output": core_output,
        "error": None,
    }


def _fail(trace_id: str, keshav_output: dict, error: str) -> dict:
    return {
        "trace_id": trace_id,
        "status": "FAIL",
        "keshav_output": keshav_output,
        "rajya_output": None,
        "sarathi_output": None,
        "core_output": None,
        "error": error,
    }
