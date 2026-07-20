# Security Validation — BHIV Phase IV

**Date:** 2026-07-13

---

## Verified controls

| Control | Implementation | Test evidence |
|---|---|---|
| API key auth | Bearer on gateway routes | Partner live captures; auth_probe |
| JWT tenant scope | HS256 client tokens | Harness + lifecycle tests |
| Tenant isolation | Cross-tenant 404 on workforce reads | `test_tenant_isolation_workforce.py` (5 pass) |
| RBAC scope resolution | `resolve_policy_scope()`, `assert_control_center_access()` | `test_control_center_governance.py` (7 pass) |
| Governance audit trail | All writes via `write_workforce_audit()` | Runtime tests |
| Secrets handling | `.env` gitignored; no secrets in captures | `ECOSYSTEM_REPOSITORY_MAP.md` §7 |

---

## Partner security notes

- Karma `stp_bridge.py`: HMAC signing + optional mTLS toward InsightFlow  
- Artha: circuit breaker on SETU pipeline (partner repo, not modified)

---

## Recommendations

- Rotate `API_KEY_SECRET` after evidence capture sessions (per prior sprint security note)  
- Do not commit partner `.env` files

---

## Not validated this phase

- Penetration test suite (`/v1/security/penetration-test`) — exists in broader test matrix but not re-run for Phase IV  
- WAF / DDoS — **TMS**
