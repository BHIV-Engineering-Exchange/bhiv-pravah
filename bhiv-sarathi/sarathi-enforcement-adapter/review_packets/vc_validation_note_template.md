# Sarathi v14.6 — Independent Validation Note (Template)

**Generated:** 2026-05-12T16:15:37.787145Z
**Sign-off owner:** Vinayak Tiwari (independent validator)

## Demo summary (auto-populated)

| # | Demo | Status | Duration | Evidence |
|---|------|--------|----------|----------|
| D1 | Multi-node deterministic execution | PASS | 62ms | `multi_node_determinism_report.json` |
| D2 | Transport mutation attempt → chain halt | PASS | 15ms | `transport_integrity_report.json` |
| D3 | Successful propagation → identical hashes across Core/InsightFlow/Bucket | PASS | 5ms | `cross_system_integration_report.json` |
| D4 | Bucket read-back exact match (5 sampled decisions) | PASS | 6ms | `bucket_state_verification_report.json` |
| D5 | 1000-iteration replay proof | PASS | 429ms | `propagation_byte_equality_report_1000.json` |

**All demos passed:** true (5/5)

## Independent Validation

I, ___________________________________ (Vinayak Tiwari), have independently
verified the artefacts referenced above on ____________ (date), using commit
______________ of the Sarathi enforcement adapter. My findings are:

- [ ] Multi-node determinism: byte-identical response hashes across 3 nodes.
- [ ] Transport integrity: byte-mutating transport attacks chain-halt; benign features pass.
- [ ] Cross-system integration: Core, InsightFlow, and Bucket received byte-identical bytes.
- [ ] Bucket readback: persisted bytes equal Sarathi's sealed bytes.
- [ ] 1000-iteration replay: `UniqueResponseHashes == 1`, `DeterminismViolations == 0`.

### Deviations observed (if any)

_Fill in any departures from expected outcomes, with reproduction steps._

### Sign-off

Signed: __________________________________________   Date: ________________

Vinayak Tiwari — Independent Validator, Sarathi v14.6
