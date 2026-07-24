#!/usr/bin/env bash
#
# scripts/preflight_clean.sh — v15.1 canonical artefact cleanup
#
# Run this BEFORE any reviewer-facing demo or any --v14-6 / --live-integration /
# --parallel-execute / --distributed-integration / --failure-demo /
# --service-live-demo run. Stale logs from earlier runs poison the v14.6
# audit's "v14_6_entries == 0" check on
# proof_logs/determinism_violation_log.jsonl.
#
# WHAT it removes:
#   live/                                 — bucket files, peer JSONL logs,
#                                            inbound nonces, trust snapshot
#                                            (operator should re-register
#                                            evaluators after a clean if any)
#   proof_logs/                           — every audit JSONL backup
#   *_results.json / *_report.json        — every harness report at repo root
#   audit_v14_6_report.{md,json}          — v14.6 audit artefacts
#   propagation_byte_equality_report*.json
#
# WHAT it keeps:
#   policies/                             — policy v1/v2 (immutable)
#   sarathi_keys.enc                      — encrypted token authority key
#   *.go / *.md / go.{mod,sum}            — source / docs
#
# Usage:
#   ./scripts/preflight_clean.sh           — clean
#   ./scripts/preflight_clean.sh --dry-run — show what would be removed
#
# TAG: v15.1 network-surface-closure

set -e

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

# Resolve the project root (one directory above this script).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

remove() {
  local target="$1"
  if [[ -e "$target" ]]; then
    if [[ "$DRY_RUN" == "1" ]]; then
      echo "[dry-run] rm -rf $target"
    else
      rm -rf "$target"
      echo "  removed: $target"
    fi
  fi
}

remove_glob() {
  local pattern="$1"
  for target in $pattern; do
    [[ -e "$target" ]] || continue
    if [[ "$DRY_RUN" == "1" ]]; then
      echo "[dry-run] rm -f $target"
    else
      rm -f "$target"
      echo "  removed: $target"
    fi
  done
}

echo "== Sarathi v15.1 preflight clean =="
echo "  root: ${ROOT_DIR}"
[[ "$DRY_RUN" == "1" ]] && echo "  mode: DRY-RUN (no files will be removed)"

# Directories
remove "live"
remove "proof_logs"
remove "multi_node_reports"

# Top-level harness reports (one shell-glob per pattern keeps wildcards safe).
remove_glob "*_results.json"
remove_glob "*_report.json"
remove_glob "*_report_1000.json"
remove_glob "audit_v14_6_report.md"
remove_glob "audit_v14_6_report.json"
remove_glob "propagation_byte_equality_report*.json"
remove_glob "live_integration_report.json"
remove_glob "service_live_integration_report.json"
remove_glob "parallel_execution_report.json"
remove_glob "distributed_integration_report.json"
remove_glob "failure_demo_report.json"
remove_glob "cross_system_integration_report.json"
remove_glob "transport_integrity_report.json"
remove_glob "multi_node_determinism_report.json"
remove_glob "governance_consistency_report.json"
remove_glob "vc_demo_*.json"
remove_glob "vc_demo_*.jsonl"
remove_glob "evaluator_registry_results.json"
remove_glob "external_decision_results.json"
remove_glob "infrastructure_enforcement_results.json"
remove_glob "system_simulation_results.json"
remove_glob "scenario_full_results.json"
remove_glob "core_simulator_results.json"
remove_glob "concurrency_stress_results.json"
remove_glob "deterministic_replay_results.json"
remove_glob "clock_drift_results.json"
remove_glob "bucket_state_verification_report.json"
remove_glob "bypass_attack_results.json"
remove_glob "attack_harness_results.json"
remove_glob "enforcement_results.json"
remove_glob "integration_gate_results.json"
remove_glob "e2e_trace_samples.json"
remove_glob "execution_trace_samples.json"
remove_glob "sarathi_run_*.log"
remove_glob "stderr.log"
remove_glob "stderr_audit.log"
remove_glob "full_output.txt"
remove_glob "out_full.txt"

echo "== preflight clean complete =="
