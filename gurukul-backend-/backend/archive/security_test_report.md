# Unauthorized Access Simulation – Security Test Report

## 1. Token Spoofing

- **Test**: Send a request with `Authorization: Bearer <forged_or_expired_jwt>`.
- **Expected**: 401 Unauthorized. JWT signature verification and expiry must be enforced; no data returned.
- **Mitigation**: Use strong `JWT_SECRET_KEY`; never disable `verify_exp`; validate algorithm (e.g. reject `alg=none`).

## 2. Tenant Spoofing

- **Test**: Valid JWT for User A (tenant 1). Send request with `X-Tenant-ID: <tenant_2_id>` or subdomain of tenant 2.
- **Expected**: 403 Forbidden – “User does not belong to this tenant.” User must be loaded from the **resolved tenant’s DB**; then enforce `user.tenant_id == resolved_tenant_id`. If they differ, reject.
- **Mitigation**: In `get_current_user` (or equivalent), after resolving tenant from request and loading user from that tenant’s DB, compare `user.tenant_id` to the resolved tenant; reject on mismatch.

## 3. Subdomain / Header Manipulation

- **Test**: Request with invalid or non-existent `X-Tenant-ID` or subdomain that does not exist in tenant registry.
- **Expected**: 400 “Tenant required” or 404 “Tenant not found” when DB router cannot resolve tenant or database_url. No fallback to default tenant in production.

## 4. IDOR Across Tenants

- **Test**: Use a resource ID from tenant A in a request resolved to tenant B (e.g. `X-Tenant-ID: B` with path param id from tenant A).
- **Expected**: 404 or empty – tenant B’s DB does not contain that ID. Isolation is enforced by using only the resolved tenant’s DB for the request.

## 5. Document Results

- Run the above tests (manual or automated) and record: **Test name**, **Expected**, **Actual**, **Pass/Fail**. Re-run after any auth or tenant-resolution change.
