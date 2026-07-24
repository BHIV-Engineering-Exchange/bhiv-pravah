# Sarathi v15.6 — Bridge Integration Contract (TANTRA Separation)

> **Audience:** Bridge team (external verifiers)  
> **System version:** v15.6 JWT Authority Layer  
> **Authority:** Sarathi Governance Kernel — Outbound Token Authority  
> **Classification:** Integration contract — forward to Bridge implementers verbatim  

---

## 1. Token Issuance Endpoint

**Endpoint:** `POST https://<sarathi>/sarathi/enforce`

There is **no separate `/token` or `/mint` endpoint**. The JWT is a side-effect of submitting a signed Sovereign 9-field decision body. On a successful `ALLOW` verdict, the HTTP response body gains three new fields:

```json
{
  "capability_token_jwt":    "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6IjM0YzkzNjBlN2MyMTdjNDUxNTUwZDgyYTc4YTIzMjFmYmUyMTllNGU4Y2E3YWJlZGJhYmQ2NDQyOGVjNGIxNjQifQ.eyJhdWQiOiJiaGl2LWNvcmUtcnVudGltZSIsImV4cCI6MTc3ODYwMjQ2NywiaWF0IjoxNzc4NjAyNDA3LCJpc3MiOiJodHRwczovL3NhcmF0aGkuYmhpdi5sb2NhbC9hdXRob3JpdHkiLCJqdGkiOiIuLi4iLCJuYmYiOjE3Nzg2MDI0MDcsInNhcmF0aGk6c2NoZW1hX3ZlcnNpb24iOiJzYXJhdGhpLmNhcGFiaWxpdHktand0L3YxLjAiLCJzYXJhdGhpOnZlcmRpY3QiOiJBTExPVyIsInN1YiI6ImRlYy10ZXN0LTAwMSJ9.<64-byte-EdDSA-sig>",
  "capability_token_kid":    "<hex64 RFC 7638 thumbprint>",
  "capability_token_issuer": "https://<sarathi>/authority"
}
```

The same path is advertised as `token_endpoint` in the OIDC-style discovery document. Old Bridge clients that ignore unknown JSON fields see no change. New Bridge clients read `capability_token_jwt` and verify it offline.

> [!IMPORTANT]
> Bridge does **NOT** call a separate token endpoint. The existing `POST /sarathi/enforce` call — the one Sovereign Core already makes — is the token mint. Bridge reads the JWT from the response.

**Source code reference:** [service_boundary_sovereign.go:211](file:///d:/sarathi1/sarathi-enforcement-adapter/service_boundary_sovereign.go#L211) — the Sovereign handler sets `X-Sarathi-Mint-JWT: 1` on the inner request, which triggers [jwt_authority_mint.go:95](file:///d:/sarathi1/sarathi-enforcement-adapter/jwt_authority_mint.go#L95) `MintJWT()`.

---

## 2. JWT Verification Details

**Wire format:** Compact RFC 7519 / RFC 7515 serialization — three base64url-encoded parts (no padding) joined by dots: `header.payload.signature`.

**Verification algorithm for Bridge (offline — no roundtrip to Sarathi):**

1. Split the JWT on `.` → parts[0]=header, parts[1]=payload, parts[2]=signature.
2. Base64url-decode parts[0] (header JSON). **Confirm `alg == "EdDSA"`**. If anything else → **REJECT** (RFC 8725 §3.1).
3. Read the `kid` field from the header. Look it up in the cached JWKS map (`kid` → `ed25519.PublicKey`). If not present → **REJECT**. Do NOT synthesize a fallback.
4. Base64url-decode parts[2] → 64-byte Ed25519 signature.
5. Verify: `ed25519.Verify(publicKey, []byte(parts[0] + "." + parts[1]), signatureBytes)`. If fails → **REJECT**.
6. Base64url-decode parts[1] (payload JSON). Validate:
   - `iss == <expected issuer URL>` (must equal what the discovery document returned)
   - `aud == "bhiv-core-runtime"` (or the deployment-specific audience)
   - Current time is within `[nbf, exp]`
7. If all pass → token is valid. Extract `sub` (decision_id), `sarathi:trace_id`, `sarathi:response_hash`, etc.

**Compatible libraries (any RFC 8037 verifier works):**
- Go: `github.com/golang-jwt/jwt/v5`
- Python: `pyjwt` (with `cryptography`), `python-jose`
- Java: `jose4j`, `nimbus-jose-jwt`
- Node.js: `jose`, `node-jose`

**Performance:** ≈ 50–100 μs per verification on commodity hardware. Zero network calls once JWKS is cached.

**Source code reference:** [jwt_authority_verify.go:97-260](file:///d:/sarathi1/sarathi-enforcement-adapter/jwt_authority_verify.go#L97-L260)

---

## 3. Issuer Value (`iss` claim)

**Default (dev):** `https://sarathi.bhiv.local/authority`

**Configurable via env:** `SARATHI_TOKEN_ISSUER`

**Production requirement:** MUST be a non-empty `https://` URL. The production boot gate (`ERR_JWT_AUTHORITY_ISSUER_INSECURE`) refuses to start with `http://`.

**Bridge MUST validate:** `iss == <expected URL>` on every token. The expected URL is the one returned by the discovery document at startup.

**Source code:**
- Default: [jwt_authority.go:97](file:///d:/sarathi1/sarathi-enforcement-adapter/jwt_authority.go#L97) — `const DefaultJWTIssuer = "https://sarathi.bhiv.local/authority"`
- Env var: [jwt_authority.go:82](file:///d:/sarathi1/sarathi-enforcement-adapter/jwt_authority.go#L82) — `EnvTokenIssuer = "SARATHI_TOKEN_ISSUER"`
- Claim population: [jwt_authority_mint.go:121](file:///d:/sarathi1/sarathi-enforcement-adapter/jwt_authority_mint.go#L121) — `"iss": a.Issuer()`

---

## 4. Signing Algorithm

**Algorithm:** `EdDSA` (RFC 8037), using **Ed25519** (RFC 8032).

**NOT RS256.** EdDSA is RFC 8725-recommended for new deployments:
- Deterministic (no random nonce needed per signature)
- Faster than RS256
- Produces 64-byte signatures (vs 256+ bytes for RS256)
- Smaller keys (32-byte public, 64-byte private vs 2048-bit RSA)

**JWT header:** `{"alg":"EdDSA","typ":"JWT","kid":"<hex64>"}`

**Bridge MUST pin:** Accept `alg: "EdDSA"` only. Reject `alg: "none"`, `HS256`, `RS256`, and everything else (RFC 8725 §3.1). The Sarathi verifier itself does this via `jwt.WithValidMethods([]string{"EdDSA"})`.

**Source code:** [jwt_authority_mint.go:143](file:///d:/sarathi1/sarathi-enforcement-adapter/jwt_authority_mint.go#L143) — `jwt.NewWithClaims(jwt.SigningMethodEdDSA, claims)`

---

## 5. Public Key / JWKS Endpoint

### 5.1 JWKS Endpoint (primary — Bridge fetches this)

**URL:** `GET https://<sarathi>/sarathi/.well-known/jwks.json`

**Content-Type:** `application/jwk-set+json`  
**Cache-Control:** `public, max-age=300` (5 minutes)  
**ETag:** SHA-256 of canonical JSON (supports conditional GET via `If-None-Match`)

**Live JWKS document shape:**

```json
{
  "schema_version": "sarathi.jwt-authority/v15.6",
  "registry_version": 1,
  "issuer": "https://sarathi.bhiv.local/authority",
  "issued_at": "2026-05-12T16:13:44Z",
  "keys": [
    {
      "kid": "34c9360e7c217c451550d82a78a2321fbe219e4e8ca7abedbabd64428ec4b164",
      "kty": "OKP",
      "crv": "Ed25519",
      "x": "-n20blueFa_FLURCtxozlATby0PqafpgQy7b4cR-V8I",
      "use": "sig",
      "alg": "EdDSA",
      "x5t#S256": "fcb003df9d1048f33f0afd6d6155840f7544551ac1768ac943f20bb6b30cdde5",
      "iat": 1778602407,
      "source": "current"
    }
  ]
}
```

**JWK fields per RFC 7517 / RFC 8037:**

| Field | Value | Notes |
|---|---|---|
| `kty` | `"OKP"` | Octet Key Pair (RFC 8037) |
| `crv` | `"Ed25519"` | Curve identifier |
| `x` | `"<base64url(32-byte-pubkey)>"` | Public key, base64url no padding |
| `alg` | `"EdDSA"` | JOSE algorithm identifier |
| `use` | `"sig"` | Signing use |
| `kid` | `"<hex64>"` | RFC 7638 thumbprint = `hex(SHA-256(canonical JWK {crv,kty,x}))` |
| `source` | `"current"` or `"grace-period"` | Rotation hint |

**During key rotation,** the `keys` array contains **two** entries: `source: "current"` (new key) and `source: "grace-period"` (old key, verify-only). The grace-period entry also has a `grace_expires` field (RFC 3339).

**Source code:** [jwt_authority_jwks.go](file:///d:/sarathi1/sarathi-enforcement-adapter/jwt_authority_jwks.go), path constant at [ecosystem_endpoints.go:245](file:///d:/sarathi1/sarathi-enforcement-adapter/ecosystem_endpoints.go#L245)

### 5.2 OIDC-Style Discovery Document (secondary — bootstrap helper)

**URL:** `GET https://<sarathi>/sarathi/.well-known/sarathi-authority`

```json
{
  "issuer": "https://sarathi.bhiv.local/authority",
  "jwks_uri": "https://<sarathi>/sarathi/.well-known/jwks.json",
  "token_endpoint": "https://<sarathi>/sarathi/enforce",
  "introspection_endpoint": "https://<sarathi>/sarathi/v1/token/introspect",
  "signing_alg_values_supported": ["EdDSA"],
  "id_token_signing_alg_values_supported": ["EdDSA"],
  "subject_types_supported": ["public"],
  "token_endpoint_auth_methods_supported": ["none"],
  "introspection_endpoint_auth_methods_supported": ["client_secret_basic"],
  "token_lifetime_seconds": 60,
  "version": "v15.6",
  "schema_version": "sarathi-authority-discovery/v1.0"
}
```

**Bridge startup flow:**
1. Fetch `GET /.well-known/sarathi-authority` → get `jwks_uri`, `issuer`, `signing_alg_values_supported`, `token_lifetime_seconds`.
2. Fetch `GET <jwks_uri>` → parse JWKS → build in-memory map `kid → ed25519.PublicKey`.
3. Cache both documents. Refresh JWKS every 5 min (Cache-Control) or on kid miss.

**Source code:** [jwt_authority_jwks.go:158-199](file:///d:/sarathi1/sarathi-enforcement-adapter/jwt_authority_jwks.go#L158-L199), path constant at [ecosystem_endpoints.go:250](file:///d:/sarathi1/sarathi-enforcement-adapter/ecosystem_endpoints.go#L250)

### 5.3 Token Introspection (optional)

**URL:** `POST https://<sarathi>/sarathi/v1/token/introspect`

RFC 7662 compliant. Bearer-auth protected (`Authorization: Bearer <SARATHI_JWT_INTROSPECTION_API_KEY>`). Returns `{"active":true|false, ...}`. Bridge calls this only when it needs per-call revocation/consumption status (rare; most calls are offline JWKS verification).

**Source code:** [jwt_authority_handlers.go:195-311](file:///d:/sarathi1/sarathi-enforcement-adapter/jwt_authority_handlers.go#L195-L311), path constant at [ecosystem_endpoints.go:255](file:///d:/sarathi1/sarathi-enforcement-adapter/ecosystem_endpoints.go#L255)

---

## 6. Sample Valid Token

### Decoded header:
```json
{"alg":"EdDSA","typ":"JWT","kid":"34c9360e7c217c451550d82a78a2321fbe219e4e8ca7abedbabd64428ec4b164"}
```

### Decoded payload (full claims set):
```json
{
  "iss": "https://sarathi.bhiv.local/authority",
  "sub": "dec-test-001",
  "aud": "bhiv-core-runtime",
  "exp": 1778602467,
  "nbf": 1778602407,
  "iat": 1778602407,
  "jti": "550e8400-e29b-41d4-a716-446655440000",
  "sarathi:decision_id":        "dec-test-001",
  "sarathi:request_hash":       "<hex64>",
  "sarathi:policy_hash":        "<hex64>",
  "sarathi:enforcement_hash":   "<hex64>",
  "sarathi:correlation_id":     "<UUIDv4>",
  "sarathi:verdict":            "ALLOW",
  "sarathi:obligations":        ["audit_log"],
  "sarathi:registry_version":   42,
  "sarathi:rpa_hash":           "<hex64>",
  "sarathi:token_hash":         "<hex64>",
  "sarathi:trace_id":           "<32-hex>",
  "sarathi:legacy_issuer":      "sarathi-enforcement-adapter",
  "sarathi:schema_version":     "sarathi.capability-jwt/v1.0",
  "sarathi:response_hash":      "<hex64, Sovereign path>",
  "sarathi:chain_binding_hash": "<hex64, Sovereign path>",
  "sarathi:decision_hash":      "<hex64, Sovereign path>"
}
```

### Signature:
64-byte Ed25519 signature, base64url-encoded (no padding).

### Compact wire format:
```
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6IjM0YzkzNjBlN2MyMTdjNDUxNTUwZDgyYTc4YTIzMjFmYmUyMTllNGU4Y2E3YWJlZGJhYmQ2NDQyOGVjNGIxNjQifQ.eyJhdWQiOiJiaGl2LWNvcmUtcnVudGltZSIsImV4cCI6MTc3ODYwMjQ2NywiaWF0IjoxNzc4NjAyNDA3LCJpc3MiOiJodHRwczovL3NhcmF0aGkuYmhpdi5sb2NhbC9hdXRob3JpdHkiLCJqdGkiOiIuLi4iLCJuYmYiOjE3Nzg2MDI0MDcsInNhcmF0aGk6c2NoZW1hX3ZlcnNpb24iOiJzYXJhdGhpLmNhcGFiaWxpdHktand0L3YxLjAiLCJzYXJhdGhpOnZlcmRpY3QiOiJBTExPVyIsInN1YiI6ImRlYy10ZXN0LTAwMSJ9.<base64url-EdDSA-sig>
```

### To generate a fresh sample live:
```bash
RESP=$(curl -sS -X POST https://<sarathi-ngrok>/sarathi/enforce \
  -H "X-API-Key: $SOVEREIGN_API_KEY" \
  -H "X-Sarathi-Trace-ID: $TRACE_ID" \
  -H "Content-Type: application/json" \
  -d @sovereign_allow_body.json)
echo "$RESP" | jq -r .capability_token_jwt
```

---

## 7. Expected Claims Format

### Standard RFC 7519 claims (always present):

| Claim | Type | Description |
|---|---|---|
| `iss` | string | Issuer URL — operator-configured via `SARATHI_TOKEN_ISSUER` |
| `sub` | string | Subject — the `decision_id` |
| `aud` | string | Audience — default `"bhiv-core-runtime"`, override via `SARATHI_TOKEN_AUDIENCE` |
| `exp` | number | Expiration (unix seconds) — always ≤ `iat + 60` |
| `nbf` | number | Not Before (unix seconds) — equals `iat` |
| `iat` | number | Issued At (unix seconds) |
| `jti` | string | JWT ID — UUIDv4, unique per mint |

### Private claims under `sarathi:` prefix (RFC 7519 §4.3):

| Claim | Type | Description |
|---|---|---|
| `sarathi:decision_id` | string | Decision identifier |
| `sarathi:request_hash` | string | SHA-256 hex of the enforcement request |
| `sarathi:policy_hash` | string | SHA-256 hex of the evaluated policy |
| `sarathi:enforcement_hash` | string | SHA-256 hex binding request+policy+verdict |
| `sarathi:correlation_id` | string | Correlation identifier (UUIDv4) |
| `sarathi:verdict` | string | Always `"ALLOW"` (tokens are never minted for DENY) |
| `sarathi:obligations` | array | Post-decision obligations (e.g. `["audit_log"]`) |
| `sarathi:registry_version` | number | Monotonic evaluator registry version |
| `sarathi:rpa_hash` | string | Request-Policy-Action binding hash |
| `sarathi:token_hash` | string | SHA-256 of the in-process capability token |
| `sarathi:trace_id` | string | W3C 32-hex trace identifier |
| `sarathi:legacy_issuer` | string | Always `"sarathi-enforcement-adapter"` |
| `sarathi:schema_version` | string | Always `"sarathi.capability-jwt/v1.0"` |
| `sarathi:response_hash` | string | Response hash (Sovereign path only) |
| `sarathi:chain_binding_hash` | string | Bucket chain binding (Sovereign path only) |
| `sarathi:decision_hash` | string | Sovereign decision hash (Sovereign path only) |

> [!NOTE]
> Bridge should treat all `sarathi:*` claims as informational context. The only claims **required** for authorization decisions are the standard RFC 7519 claims (`iss`, `aud`, `exp`, `nbf`) + the signature verification. The private claims exist for audit trail binding and cross-system correlation.

---

## 8. Failure Test: Sarathi Intentionally Unavailable

### How to run:

```bash
./sarathi-enforcement-adapter.exe --failure-demo
```

### What happens (Scenario 4: `sarathi_unavailable_for_bridge`):

The failure demo runner (`failure_demo_runner.go`, lines 573-693) executes this exact sequence:

1. **Authority A boots** — a JWTAuthority with a real Ed25519 keypair is created in-process.
2. **Bridge caches the JWKS** — `BuildJWKSDocument()` is called to produce the cached key set (exactly what Bridge would have fetched at startup).
3. **Sarathi "goes offline"** — the only handle that could refresh the JWKS is destroyed (simulates a network partition / cold service).
4. **Attacker presents a forged JWT** — signed by a *different* Ed25519 key. The forged token has the correct `iss`, `aud`, and valid timestamps, but a different `kid`.
5. **Bridge verifies against cached JWKS ONLY** — calls `VerifyJWT()` with the forged token. The verifier resolves `kid` against the cached key set, finds no match, and **rejects with `ERR_JWT_KID_UNKNOWN`**.
6. **No local mint, no fallback** — the Bridge-mock has no path to produce or accept the token.

### Pass criterion:

```
observed_error_code = ERR_JWT_KID_UNKNOWN  (or ERR_JWT_SIGNATURE_INVALID)
passed = true
```

### Verification:

```bash
# After running --failure-demo:
cat failure_demo_report.json | jq ".scenarios_passed, .scenarios_total"
# Expected: 4, 4

jq 'select(.scenario=="sarathi_unavailable_for_bridge")' \
   proof_logs/failure_demo_observations.jsonl
# Expected: passed:true, observed_error_code is a fail-closed reject
```

### What this proves for Bridge:

> [!IMPORTANT]
> When Sarathi is unavailable and Bridge's JWKS cache cannot resolve the `kid` of a presented token, Bridge **MUST** block the request. There is no local generation path, no fallback path, no "accept if unable to verify" path. This is the exact TANTRA separation guarantee.

**Source code:** [failure_demo_runner.go:573-693](file:///d:/sarathi1/sarathi-enforcement-adapter/failure_demo_runner.go#L573-L693)

---

## Summary: Endpoint Quick Reference

| Purpose | Method | Path | Auth |
|---|---|---|---|
| **Token issuance** (via enforce) | `POST` | `/sarathi/enforce` | `X-API-Key` + Ed25519 signature in body |
| **JWKS** (public key set) | `GET` | `/sarathi/.well-known/jwks.json` | None (public) |
| **Discovery** (OIDC-style) | `GET` | `/sarathi/.well-known/sarathi-authority` | None (public) |
| **Introspection** (optional) | `POST` | `/sarathi/v1/token/introspect` | `Authorization: Bearer <api-key>` |
| **Token validation** (self-test) | `GET` | `/sarathi/validate-token?token=<jwt>` | None |

## Summary: Cryptographic Parameters

| Parameter | Value |
|---|---|
| Algorithm | `EdDSA` (Ed25519, RFC 8032 / RFC 8037) |
| Signature size | 64 bytes |
| Public key size | 32 bytes |
| Key type | `OKP` (Octet Key Pair) |
| Curve | `Ed25519` |
| kid derivation | RFC 7638 thumbprint = `hex(SHA-256({"crv":"Ed25519","kty":"OKP","x":"<base64url(pub)>"}))` |
| Token TTL | ≤ 60 seconds (configurable down, never up) |
| JWKS cache | `Cache-Control: public, max-age=300` (5 min) |
| Wire format | RFC 7519 compact serialization (RFC 7515 JWS) |

## RFC Compliance Matrix

| RFC | Coverage |
|---|---|
| **7519** (JWT) | Compact serialization; `iss/sub/aud/exp/nbf/iat/jti`; `sarathi:` private claims per §4.3 |
| **7517** (JWK/JWKS) | `keys` array; every required field |
| **7515** (JWS) | `golang-jwt/jwt/v5` produces RFC 7515 compact form |
| **8037** (EdDSA in JOSE) | `alg=EdDSA`, `kty=OKP`, `crv=Ed25519`, `x` = base64url(pubkey) |
| **7662** (Introspection) | POST form body; `active` boolean; bearer auth; opaque-on-failure |
| **8725** (JWT BCP) | `alg=none` rejected; algorithm pinned via `jwt.WithValidMethods`; iss/aud validated; ≤60s TTL |
| **8414** (Server Metadata) | Discovery doc adapted; `token_endpoint=/sarathi/enforce` |
| **7638** (JWK Thumbprint) | kid = canonical JWK thumbprint over `{crv, kty, x}` |
| **8032** (Ed25519) | Existing keypair format |
