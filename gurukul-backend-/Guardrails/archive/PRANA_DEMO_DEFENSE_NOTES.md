# PRANA Demo Defense Notes

## Purpose

Quick reference for defending PRANA during demos, audits, or reviews. Provides concise responses to common questions.

---

## Core Defense Points

- **Observational only** - Observes signals, emits states. No interpretation or decisions.
- **Non-authoritative** - Packets are observations, not facts. Cannot be used as evidence.
- **Fail-open safely** - All failures → Silent cessation. No application impact.

---

## Common Questions and Responses

### "What does PRANA observe?"
**Response:** "Aggregate signal counts only: keyboard, mouse, scroll, focus, route, search, content. No event content, sequences, or semantics. Individual events discarded after counting."

### "What do states represent?"
**Response:** "Observational classifications from signal patterns. Not user behavior, intent, or productivity. Deterministic: same signals → same state."

### "Can PRANA identify users?"
**Response:** "No. System_id identifies system instances, not users. Not personally identifiable. Cannot track or correlate users."

### "Can PRANA prove user activity?"
**Response:** "No. Packets prove only that PRANA observed signals. Signals may be automated. Cannot prove user activity, intent, or behavior."

### "Can PRANA be used for surveillance?"
**Response:** "No. Aggregate counts only (no content), system_id not personally identifiable, no behavior reconstruction, no cross-session correlation. Replay is read-only access to pre-aggregated values, not surveillance."

### "Can PRANA be used for policy evaluation?"
**Response:** "No. Zero context about intent or compliance. Observes signals, not behaviors. States are observations, not evaluations."

### "What happens when PRANA fails?"
**Response:** "Fails-open safely. Silent operation cessation. No retry, no queue, no persistence. No application impact. Failures are operational events, not diagnostic events."

### "Can PRANA packets be used as evidence?"
**Response:** "No. Telemetry, not audit logs. Lack cryptographic authenticity, integrity, and non-repudiation. Non-authoritative. Cannot be used as evidence."

### "What if packets are lost or corrupted?"
**Response:** "PRANA discards failed packets and continues. Non-critical infrastructure. Fail-open ensures no application impact."

### "Can replay enable retroactive judgment?"
**Response:** "No. Replay enables read-only access to pre-aggregated telemetry values, not judgment. Historical observations, not facts. Cannot prove past behavior or compliance."

---

## Red Flags to Watch For

**"PRANA tracks users"** → "Observes signals from system instances. System_id not personally identifiable."

**"States prove productivity"** → "States are observational classifications, not productivity indicators."

**"Packets are audit logs"** → "Telemetry, not audit logs. No cryptographic guarantees."

**"Replay enables surveillance"** → "Read-only access to pre-aggregated telemetry values, not surveillance. Cannot track or identify users."

**"Failures indicate problems"** → "Operational events, not diagnostic events. Do not indicate problems or violations."

---

## Quick Reference Phrases

- **"Observational only"** - Observes, does not interpret or decide
- **"Non-authoritative"** - Observations, not facts
- **"Fail-open"** - Failures result in silent cessation, no impact
- **"Aggregate counts only"** - No content, sequences, or semantics
- **"System instance, not user"** - System_id not personally identifiable
- **"Telemetry, not audit logs"** - No cryptographic guarantees, cannot be evidence
- **"Read-only access, not surveillance"** - Replay enables read-only access to pre-aggregated values, not tracking

---

## Summary

PRANA is **safe, boring infrastructure**:
- Observational only (no interpretation or decisions)
- Non-authoritative (observations, not facts)
- Fail-open safely (no application impact)
- Privacy-preserving (aggregate counts, no user identification)
- Non-enforcing (no control or enforcement capabilities)
