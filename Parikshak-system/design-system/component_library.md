# BHIV Command Center Design System — Component Library

This document specifies the 10 reusable visual primitives implemented across Parikshak.

## Reusable Component Primitives

### 1. Review Card
Renders a complete candidate submission summary including overall verdict, readiness percentage, score gauge, and technical quality indicators.

### 2. Task Card
Displays a detailed BHIV task assignment including dharma/purpose, prerequisites, next tasks, expected runtime, deliverables, and acceptance criteria.

### 3. Evidence Card
Renders a verified runtime file trace list with type tag, copyable path name, size/time metrics, and verification badge.

### 4. Trace Card
Renders trace lineage envelopes, governance actor signature, and cryptographic token verification statuses.

### 5. Replay Card
Displays replay execution logs, parent/current hash alignment, and deterministic replay match percentages.

### 6. Timeline Card
Tracks a candidate task through the engineering stages: Task -> Review -> Testing -> Fixes -> Approval -> Assignment.

### 7. Risk Card
Displays risk items from the risk register: risk type, severity levels (Critical, High, Medium, Low), impact description, and mitigations.

### 8. Metric Card
Universal key value metric display with visual thresholds, gauges, and comparison arrows (e.g. throughput, assignment rates).

### 9. Assignment Card
Allocates assignments: suggested owner, skill match %, load status, dependencies, and execution button.

### 10. Candidate Card
Candidate profile block containing name, performance history, active skills, and direct link to their timeline.
