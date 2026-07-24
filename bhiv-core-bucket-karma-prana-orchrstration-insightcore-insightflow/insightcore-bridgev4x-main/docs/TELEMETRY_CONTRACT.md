## Telemetry Contract — v4.x

Fields:
- service: fixed string ("InsightBridge")
- version: pinned version string
- timestamp: unix seconds
- decision: ALLOW | DENY
- reason: stable reason code

Guarantees:
- One telemetry event per request
- No free-form text
- Deterministic values only
