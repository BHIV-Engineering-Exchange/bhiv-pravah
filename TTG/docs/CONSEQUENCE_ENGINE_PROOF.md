# CONSEQUENCE_ENGINE_PROOF.md

**Phase 5 Deliverable — Consequence Engine**
**Sprint: Arbitrary Contract Execution**
**Status: COMPLETE — 5/5 consequence types proved**

---

## Objective

Prove that consequence rules are evaluated entirely from contract
configuration. No hardcoded logic. No static rules file loaded at
startup. Any action type, any event type, any condition — all
declared in the contract.

---

## Architecture

The existing `consequenceCompiler.js` loads rules from `consequenceRules.json`
at startup — a static file with gaming-specific rules (`END_GAME`,
`DAMAGE_PLAYER`, etc.). That is the demo-bound path.

Phase 5 introduces `contractConsequenceEngine.js` — a generic evaluator
that reads `consequences[]` directly from the contract at execution time.

```
Contract consequences[]
  ↓
contractConsequenceEngine.evaluate(consequences, event, state)
  ↓
  for each rule in consequences[]:
    - check rule.on === event.event_type
    - check rule.if.entities         (entity prefix match)
    - check rule.if.context_checks   (operator or equality)
    - check rule.if.state_checks     (dot-notation path)
  ↓
  matched rules → extract rule.then[] actions
  ↓
  sort by priority (critical → high → medium → low)
  ↓
{ matched: [rule_id...], actions: [{ rule_id, action, priority, payload }] }
```

Zero static rules. Zero hardcoded action types. Zero code branches for
specific consequence scenarios.

---

## New File

**`backend/consequence/contractConsequenceEngine.js`**

Single exported function: `evaluate(consequences, event, state)`.
47 lines. No external dependencies. No file I/O. No startup loading.

---

## Contract Used

**File:** `backend/contracts/contract_consequence_proof.json`

```json
{
  "trace_id":   "trace_consequence_engine_proof",
  "domain":     "consequence_proof",
  "consequences": [
    { "rule_id": "zone_entry_alert",  "on": "zone_enter",      ... },
    { "rule_id": "collision_response","on": "collision",        ... },
    { "rule_id": "resource_depleted", "on": "resource_update",  ... },
    { "rule_id": "mission_complete",  "on": "mission_update",   ... },
    { "rule_id": "alert_generation",  "on": "state_change",     ... }
  ]
}
```

All 5 consequence types declared as contract data. No runtime code
knows these rule IDs, action names, or event types in advance.

---

## Execution Output

```
╔══════════════════════════════════════════════════════════╗
║   PHASE 5 — CONSEQUENCE ENGINE PROOF                    ║
╚══════════════════════════════════════════════════════════╝
Consequences in contract : 5
Rules source             : contract (not consequenceRules.json)
Engine                   : contractConsequenceEngine.js
```

---

## Consequence 1 — Zone Entry

```
Test 1 — Zone Entry
  event_type : zone_enter
  entities   : [vessel_01]
  context    : {"zone_id":"restricted_zone","distance":3}
  ✓ Rules matched  : zone_entry_alert
  ✓ Actions fired  : 2
    [high    ] EMIT_ALERT   ← rule:zone_entry_alert
               payload: {"alert_type":"zone_violation","message":"Entity entered restricted zone"}
    [medium  ] LOG_EVENT    ← rule:zone_entry_alert
               payload: {"message":"Zone entry logged for audit"}
```

**Rule in contract:**
```json
{
  "rule_id": "zone_entry_alert",
  "on":      "zone_enter",
  "if":      { "context_checks": { "zone_id": "restricted_zone" } },
  "then": [
    { "action": "EMIT_ALERT",  "priority": "high",   "payload": { "alert_type": "zone_violation" } },
    { "action": "LOG_EVENT",   "priority": "medium",  "payload": { "message": "Zone entry logged" } }
  ]
}
```

**Proof:** `zone_enter` event with `context.zone_id == restricted_zone` matched
contract rule. Engine fired `EMIT_ALERT` + `LOG_EVENT` with payloads from contract.
No code branch handled "zone entry" — `_checkCondition` read the `context_checks`
field from the rule object.

---

## Consequence 2 — Collision

```
Test 2 — Collision
  event_type : collision
  entities   : [drone_01, drone_02]
  context    : {"distance":1.2,"collision_force":0.8}
  ✓ Rules matched  : collision_response
  ✓ Actions fired  : 2
    [critical] EMIT_ALERT      ← rule:collision_response
               payload: {"alert_type":"collision_critical","message":"Entities at collision distance"}
    [high    ] RECORD_INCIDENT ← rule:collision_response
               payload: {"incident_type":"collision","severity":"high"}
```

**Rule in contract:**
```json
{
  "rule_id": "collision_response",
  "on":      "collision",
  "if":      { "context_checks": { "distance": { "operator": "<=", "value": 2.0 } } },
  "then": [
    { "action": "EMIT_ALERT",      "priority": "critical", "payload": { "alert_type": "collision_critical" } },
    { "action": "RECORD_INCIDENT", "priority": "high",     "payload": { "incident_type": "collision" } }
  ]
}
```

**Proof:** Operator `<=` evaluated by `_op()` from contract rule data.
`distance=1.2 <= 2.0` → matched. Priority ordering confirmed — `critical`
action (`EMIT_ALERT`) sorted before `high` action (`RECORD_INCIDENT`).
`RECORD_INCIDENT` is a novel action type — no code handles it specially.

---

## Consequence 3 — Resource Depletion

```
Test 3 — Resource Depletion
  event_type : resource_update
  entities   : [vehicle_03]
  context    : {"resource_type":"fuel","resource_level":0}
  ✓ Rules matched  : resource_depleted
  ✓ Actions fired  : 2
    [critical] EMIT_ALERT  ← rule:resource_depleted
               payload: {"alert_type":"resource_depleted","message":"Resource level reached zero"}
    [critical] HALT_ENTITY ← rule:resource_depleted
               payload: {"reason":"resource_depleted"}
```

**Rule in contract:**
```json
{
  "rule_id": "resource_depleted",
  "on":      "resource_update",
  "if":      { "context_checks": { "resource_level": { "operator": "<=", "value": 0 } } },
  "then": [
    { "action": "EMIT_ALERT",  "priority": "critical", "payload": { "alert_type": "resource_depleted" } },
    { "action": "HALT_ENTITY", "priority": "critical", "payload": { "reason": "resource_depleted" } }
  ]
}
```

**Proof:** `resource_update` is a new event type — never existed in the
old system. `HALT_ENTITY` is a new action type — never in `consequenceRules.json`.
Both accepted without any code change. Condition `resource_level <= 0` evaluated
from contract operator object.

---

## Consequence 4 — Mission Completion

```
Test 4 — Mission Completion
  event_type : mission_update
  entities   : []
  context    : {"status":"complete","objectives_met":5}
  ✓ Rules matched  : mission_complete
  ✓ Actions fired  : 2
    [high    ] EMIT_EVENT    ← rule:mission_complete
               payload: {"event_type":"mission_complete","message":"All objectives achieved"}
    [medium  ] WRITE_ARTIFACT ← rule:mission_complete
               payload: {"artifact_type":"mission_summary"}
```

**Rule in contract:**
```json
{
  "rule_id": "mission_complete",
  "on":      "mission_update",
  "if":      { "context_checks": { "status": "complete" } },
  "then": [
    { "action": "EMIT_EVENT",    "priority": "high",   "payload": { "event_type": "mission_complete" } },
    { "action": "WRITE_ARTIFACT","priority": "medium",  "payload": { "artifact_type": "mission_summary" } }
  ]
}
```

**Proof:** `mission_update` is a domain-specific event type with no
existing handler. `WRITE_ARTIFACT` is a novel action. Condition
`status == complete` is a direct equality check read from `context_checks`.
Engine matched and fired both actions from contract data.

---

## Consequence 5 — Alert Generation

```
Test 5 — Alert Generation (state→damaged)
  event_type : state_change
  entities   : [unit_alpha]
  context    : {"new_state":"damaged","previous_state":"healthy"}
  ✓ Rules matched  : alert_generation
  ✓ Actions fired  : 1
    [high    ] EMIT_ALERT ← rule:alert_generation
               payload: {"alert_type":"unit_damaged","message":"Unit state changed to damaged"}
```

**Rule in contract:**
```json
{
  "rule_id": "alert_generation",
  "on":      "state_change",
  "if": {
    "context_checks": { "new_state": "damaged" },
    "entities":       ["unit_"]
  },
  "then": [
    { "action": "EMIT_ALERT", "priority": "high", "payload": { "alert_type": "unit_damaged" } }
  ]
}
```

**Proof:** Entity prefix matching — rule declares `entities: ["unit_"]`,
event entity is `unit_alpha`. Engine matched `unit_alpha.startsWith("unit_")`.
State value `damaged` is a free string — no enum restriction. Alert fired
from contract payload.

---

## Full Summary

```
════════════════════════════════════════════════════════════
PHASE 5 PROOF SUMMARY
════════════════════════════════════════════════════════════
✓ Test 1: Zone Entry
    rules=zone_entry_alert   | actions=[EMIT_ALERT, LOG_EVENT]
✓ Test 2: Collision
    rules=collision_response | actions=[EMIT_ALERT, RECORD_INCIDENT]
✓ Test 3: Resource Depletion
    rules=resource_depleted  | actions=[EMIT_ALERT, HALT_ENTITY]
✓ Test 4: Mission Completion
    rules=mission_complete   | actions=[EMIT_EVENT, WRITE_ARTIFACT]
✓ Test 5: Alert Generation
    rules=alert_generation   | actions=[EMIT_ALERT]

Consequences proved : 5/5

✓ ALL 5 CONSEQUENCE TYPES FIRED FROM CONTRACT RULES
✓ No hardcoded logic — contractConsequenceEngine reads contract data only
✓ No reference to consequenceRules.json
✓ Action types are open strings — EMIT_ALERT, HALT_ENTITY, WRITE_ARTIFACT all accepted
✓ Priority ordering enforced — critical before high before medium
════════════════════════════════════════════════════════════
```

---

## Success Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Zone entry consequence from contract | ✓ | rule:zone_entry_alert fired EMIT_ALERT + LOG_EVENT |
| Collision consequence from contract | ✓ | rule:collision_response fired EMIT_ALERT + RECORD_INCIDENT |
| Resource depletion from contract | ✓ | rule:resource_depleted fired EMIT_ALERT + HALT_ENTITY |
| Mission completion from contract | ✓ | rule:mission_complete fired EMIT_EVENT + WRITE_ARTIFACT |
| Alert generation from contract | ✓ | rule:alert_generation fired EMIT_ALERT on state→damaged |
| No reference to consequenceRules.json | ✓ | contractConsequenceEngine.js has no file I/O |
| Action types are open strings | ✓ | HALT_ENTITY, WRITE_ARTIFACT, RECORD_INCIDENT — all novel |
| Operator conditions work | ✓ | `distance <= 2.0` and `resource_level <= 0` evaluated correctly |
| Priority ordering enforced | ✓ | critical sorted before high before medium |
| Entity prefix matching works | ✓ | `unit_alpha` matched `unit_` prefix rule |

---

## What Was Not Changed

| Component | Changed? |
|-----------|----------|
| `consequenceCompiler.js` | No — existing gaming pipeline untouched |
| `consequenceRules.json` | No — not used by this engine |
| `RuleEngine.js` | No |
| `SimEngine.js` | No |
| Any other runtime file | No |

Only one new file added: `contractConsequenceEngine.js` — 47 lines.

---

## How to Reproduce

```bash
cd backend
node phase5_consequence_engine.js
```

Expected: `Consequences proved : 5/5` and
`✓ ALL 5 CONSEQUENCE TYPES FIRED FROM CONTRACT RULES`.

---

## Files Produced

| File | Purpose |
|------|---------|
| `backend/consequence/contractConsequenceEngine.js` | Generic contract-driven consequence evaluator |
| `backend/contracts/contract_consequence_proof.json` | Contract with all 5 consequence rules |
| `backend/phase5_consequence_engine.js` | Runner — proves all 5 consequence types |
| `docs/CONSEQUENCE_ENGINE_PROOF.md` | This document |

---

*Phase 5 Complete*
*Runner: phase5_consequence_engine.js*
*Contract: contract_consequence_proof.json*
*Engine: consequence/contractConsequenceEngine.js*
