# Dashboard Capability Library — BHIV Phase IV

**Date:** 2026-07-13  
**Location:** `frontend/src/components/cards/`  
**Constitutional model:** Observability ≠ Authority · Replay ≠ Execution · Dashboard ≠ Governance

---

## Primitives

| Component | File | Purpose | Primary zones |
|---|---|---|---|
| Executive Metric Card | `ExecutiveMetricCard.tsx` | Scanable KPIs with optional delta | Executive, Hiring, Workforce, Growth, Org; portal dashboards |
| Telemetry Card | `TelemetryCard.tsx` | Service health / endpoint attribution | Executive (Gateway, Agent, LangGraph) |
| Replay Card | `ReplayCard.tsx` | Read-only replay summary | Replay zone |
| Governance Card | `GovernanceCard.tsx` | Policy/decision visibility | Governance zone |
| Escalation Card | `EscalationCard.tsx` | Pending challenges | Governance zone |
| Timeline Card | `TimelineCard.tsx` | Ordered audit/trace events | Replay, Governance |
| Alert Card | `AlertCard.tsx` | Threshold / attention surface | Any zone with alert severity |
| Map Card | `MapCard.tsx` | Hierarchy / topology map | Org visibility |

---

## Shared props (`types.ts`)

```typescript
interface ConstitutionalCardProps {
  label: string
  value: string | number
  sublabel?: string
  delta?: string
  deltaPositive?: boolean
  severity?: 'normal' | 'warning' | 'alert'
  sourceSystem?: string
  correlationId?: string
  readOnly?: boolean  // default true
  disclaimer?: string
}
```

Default disclaimer: `Observability only — not execution authority` (`cardStyles.ts`).

---

## Wiring map (before → after)

| File | Before | After |
|---|---|---|
| `ControlCenter.tsx` | Generic `KpiCard` + `KpiPill` | `ConstitutionalKpiRenderer` + zone-specific primitives |
| `recruiter/Dashboard.tsx` | `StatsCard` | `StatsCard` → `ExecutiveMetricCard` adapter |
| `client/ClientDashboard.tsx` | `StatsCard` | Same adapter |
| `candidate/Dashboard.tsx` | Inline stat divs | `ExecutiveMetricCard` |

---

## Export barrel

`frontend/src/components/cards/index.ts` exports all primitives and types.

---

## Live data preservation

`ControlCenterLiveData` fetch layer unchanged — only presentation components replaced. Endpoints: `frontend/src/services/api.ts`.

---

## Verification

- `tests/e2e/control_center/test_control_center_offline.py` — re-run after refactor  
- Manual: governance panel requires `VITE_ENABLE_GOVERNANCE=true`
