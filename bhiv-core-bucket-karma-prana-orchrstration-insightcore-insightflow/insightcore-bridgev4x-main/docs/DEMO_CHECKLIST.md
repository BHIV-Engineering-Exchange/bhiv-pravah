## Enforcement Semantics — InsightBridge v4.x

ALLOW
- Token valid
- Token not expired
- iat not in future
- Nonce not previously seen

DENY / REJECT
- Any validation failure
- Replay detected
- Any internal error

Fail-Closed Guarantee
- No request is accepted unless all checks pass
- Any exception results in DENY
- No partial acceptance is possible
