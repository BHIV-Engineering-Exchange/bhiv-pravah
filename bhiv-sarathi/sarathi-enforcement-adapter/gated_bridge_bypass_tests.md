# Sarathi Gated Bridge — Bypass Attack Test Report v5.0

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Gated Bridge Bypass Tests (v5.0)
**Host Organization:** Blackhole Infiverse (BHIV)
**Result:** 20/20 bypass attacks BLOCKED

---

## Test Results

All 20 bypass attack vectors were tested in `core_simulator.go` Phase 3.

| Test | Attack | CVE/Pattern | Verdict | Block Reason |
|------|--------|-------------|---------|-------------|
| BYP-01 | Unregistered caller system | CVE-2023-22515 | DENY | UNREGISTERED_CALLER |
| BYP-02 | Empty caller system | Null credential | DENY | MISSING_CALLER_SYSTEM |
| BYP-03 | Suspended caller reuse | Okta LAPSUS$ | DENY | CALLER_SUSPENDED |
| BYP-04 | Permission escalation | AWS confused deputy | DENY | CALLER_PERMISSION_DENIED |
| BYP-05 | Inactive bridge bypass | CVE-2024-3400 | DENY | BRIDGE_INACTIVE |
| BYP-06 | SQL injection in agent_id | Classic SQLi | DENY | Agent not registered |
| BYP-07 | JNDI injection in resource_id | CVE-2021-44228 | DENY | Resource not found |
| BYP-08 | Unicode homoglyph spoofing | IDN homograph | DENY | Agent not registered |
| BYP-09 | Oversized payload DoS | CVE-2023-44487 | DENY | Input size validation |
| BYP-10 | Replay with same correlation_id | OAuth2 replay | BLOCKED | Different enforcement hashes |
| BYP-11 | Cross-caller impersonation | Storm-0558 | DENY | CALLER_PERMISSION_DENIED |
| BYP-12 | Nil/partial request | Null dereference | DENY | Validation failed |
| BYP-13 | Action injection (ClassLoader) | CVE-2022-22965 | DENY | Invalid action |
| BYP-14 | Timing attack (5 rapid requests) | Race condition | BLOCKED | All consistent ALLOW |
| BYP-15 | Header injection in version | HTTP splitting | BLOCKED | No crash, no injection |
| BYP-16 | Path traversal via admin | SolarWinds | DENY | Agent not registered |
| BYP-17 | Command injection in corr_id | GitHub Actions | BLOCKED | Data not executed |
| BYP-18 | Policy version downgrade | TLS downgrade | DENY | Version mismatch |
| BYP-19 | TOCTOU race (suspension) | Race condition | BLOCKED | Consistent snapshot |
| BYP-20 | Empty action as wildcard | Empty parameter | DENY | Missing/invalid action |

---

## Defense Layers

Each attack is stopped by one or more of these layers:

1. **Bridge Authentication** — BYP-01, BYP-02, BYP-03
2. **Bridge Permissions** — BYP-04, BYP-11
3. **Bridge Active Check** — BYP-05
4. **Input Validation** — BYP-06, BYP-07, BYP-08, BYP-09, BYP-13, BYP-20
5. **Anti-Replay** — BYP-10 (unique nonce per evaluation)
6. **Service Validation** — BYP-12, BYP-15, BYP-16, BYP-17
7. **Policy Binding** — BYP-18
8. **Concurrency Safety** — BYP-14, BYP-19 (mutex-protected operations)
