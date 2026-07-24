# COMPONENT LIBRARY

# SVACS Unified Core

## Dashboard Component Library

---

# OVERVIEW

The SVACS dashboard uses a reusable component-driven architecture designed for operational cognition visibility and replay-safe observability.

The component system supports:

* operational telemetry visibility
* replay-safe runtime inspection
* reusable dashboard primitives
* cognition-safe layout density
* deterministic runtime visibility
* operational zoning

---

# CORE DASHBOARD COMPONENTS

| Component             | Responsibility                |
| --------------------- | ----------------------------- |
| Replay Card           | Replay continuity visibility  |
| Telemetry Card        | Runtime telemetry visibility  |
| Vessel Card           | Vessel runtime inspection     |
| TTG Card              | TTG runtime participation     |
| Alert Card            | Operational alerts            |
| Lineage Card          | Lineage continuity visibility |
| Executive Metric Card | Executive operational metrics |
| Geo Card              | Geo provenance visibility     |

---

# PRIMITIVE COMPONENTS

## Panel

Reusable operational container.

Supports:

* title rendering
* runtime grouping
* telemetry zoning
* replay-safe visibility

---

## StatusDot

Operational runtime status indicator.

Supported states:

* live
* degraded
* offline
* replaying
* failed

---

## RuntimeTable

Reusable deterministic telemetry table.

Supports:

* lineage visibility
* replay inspection
* runtime metrics
* trace continuity

---

## MetricCard

Operational metric visualization component.

Supports:

* executive metrics
* runtime counters
* throughput metrics
* latency visibility

---

# PIPELINE COMPONENTS

## PipelineFlow

Visual deterministic runtime chain renderer.

Displays:

```text
SIGNAL
→ GEO
→ PERCEPTION
→ INTELLIGENCE
→ STATE
→ BUCKET
→ REPLAY
→ DASHBOARD
```

---

## ReplayTimeline

Replay-safe runtime timeline visualization.

Supports:

* replay continuity
* stage reconstruction
* deterministic playback visibility

---

# AIS COMPONENTS

## VesselRuntimeCard

Displays:

* vessel metadata
* operational role
* propulsion metadata
* runtime telemetry
* AIS participation

---

# TTG COMPONENTS

## TTGRuntimeCard

Displays:

* TTG operational visibility
* replay linkage
* runtime telemetry
* simulation continuity

---

# OBSERVABILITY GUARANTEES

Dashboard components remain:

```text
OBSERVABILITY ONLY
```

No component exposes:

* governance mutation
* replay mutation
* execution authority
* lineage modification

---

# DESIGN PRINCIPLES

The dashboard component system follows:

* low-scroll density
* operational zoning
* cognition hierarchy
* reusable primitives
* replay-safe visibility
* deterministic rendering discipline

---

# FINAL COMPONENT STATUS

```text
COMPONENT LIBRARY STATUS: ACTIVE
REUSABILITY STATUS: VERIFIED
OPERATIONAL COGNITION: ACTIVE
REPLAY SAFETY: VERIFIED
```
