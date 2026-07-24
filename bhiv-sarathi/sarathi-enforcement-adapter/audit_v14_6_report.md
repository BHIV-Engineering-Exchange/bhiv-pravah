# Sarathi v14.6 — Audit Report

Generated: 2026-05-12T16:15:38.307213Z

**Total checks:** 22  **Passed:** 22  **Failed:** 0  **All passed:** true

| # | Artefact | Field | Expected | Got | Verdict |
|---|----------|-------|----------|-----|---------|
| 1 | `bucket_state_verification_report.json` | `mismatches` | `0` | `0` | PASS |
| 2 | `bucket_state_verification_report.json` | `matches` | `>=100` | `100` | PASS |
| 3 | `bucket_state_verification_report.json` | `bucket_state_verified` | `true` | `true` | PASS |
| 4 | `clock_drift_results.json` | `unique_stable_hash_set_size` | `1` | `1` | PASS |
| 5 | `clock_drift_results.json` | `drift_detected` | `false` | `false` | PASS |
| 6 | `clock_drift_results.json` | `scenario_count` | `>=7` | `7` | PASS |
| 7 | `cross_system_integration_report.json` | `cross_system_integration_verified` | `true` | `true` | PASS |
| 8 | `cross_system_integration_report.json` | `bucket_readback_verified` | `true` | `true` | PASS |
| 9 | `cross_system_integration_report.json` | `targets_verified` | `3` | `3` | PASS |
| 10 | `multi_node_determinism_report.json` | `all_byte_identical` | `true` | `true` | PASS |
| 11 | `multi_node_determinism_report.json` | `len(unique_response_hash_stable)` | `1` | `1` | PASS |
| 12 | `multi_node_determinism_report.json` | `node_count` | `>=3` | `3` | PASS |
| 13 | `proof_logs/determinism_violation_log.jsonl` | `v14_6_entries` | `0` | `0` | PASS |
| 14 | `propagation_byte_equality_report_1000.json` | `iterations` | `1000` | `1000` | PASS |
| 15 | `propagation_byte_equality_report_1000.json` | `determinism_violations` | `0` | `0` | PASS |
| 16 | `propagation_byte_equality_report_1000.json` | `len(unique_response_hashes)` | `1` | `1` | PASS |
| 17 | `propagation_byte_equality_report_1000.json` | `all_byte_identical` | `true` | `true` | PASS |
| 18 | `transport_integrity_report.json` | `scenarios_passed + scenarios_halted_as_expected` | `8` | `8` | PASS |
| 19 | `transport_integrity_report.json` | `transport_integrity_verified` | `true` | `true` | PASS |
| 20 | `transport_integrity_report.json` | `mismatched_expected` | `0` | `0` | PASS |
| 21 | `vc_demo_results.json` | `demos_passed` | `5` | `5` | PASS |
| 22 | `vc_demo_results.json` | `all_passed` | `true` | `true` | PASS |

