# SAMPADA Human-Centric Growth Model

**Status**: Draft  
**Owner**: Rishabh Yadav (authority and sign-off required)  
**Maintained by**: Shashank (Sampada, Support Builder)  
**Last Updated**: 2026-05-30  

---

## Purpose

This document defines the human-centric growth philosophy, balanced framework, and guardrails that govern how Sampada surfaces employee growth signals. It is binding on all dashboard, analytics, and observability features that touch employee data.

> **Core Mandate**: Growth visibility must empower humans — never coerce, rank, or surveil them.

---

## 1. Design Principles

These four principles are **non-negotiable** and must be actively enforced at every layer of the system — from data model to UI.

### 1.1 Growth ≠ Pressure

Growth signals exist to help employees understand their trajectory and identify opportunities. They must **never** be weaponised to create productivity pressure, enforce output quotas, or generate punitive signals.

- ✅ Allowed: "You completed 3 learning modules this month — great momentum!"
- ❌ Prohibited: "You completed 3 learning modules — 40% below team average."

### 1.2 Metrics ≠ Human Worth

No metric, score, or growth indicator may be used to assign or imply a judgment of a person's inherent value, worth, or competence.

- ✅ Allowed: Skill trajectory maps that highlight growth over time.
- ❌ Prohibited: A single composite "employee score" ranking humans against each other.

### 1.3 Visibility ≠ Surveillance

Displaying growth data is not the same as monitoring behaviour. The system must distinguish between **invited visibility** (employee-initiated sharing) and **imposed observation** (covert monitoring).

- ✅ Allowed: Manager can see team-level learning completion rates (aggregated, non-PII).
- ❌ Prohibited: Manager can see moment-by-moment activity logs for each individual.

### 1.4 Analytics ≠ Coercion

Analytics surfaces insights — it does not issue mandates. All growth data is advisory. Execution decisions remain with humans (managers, employees, HR).

- ✅ Allowed: "Skill gap alert: Team missing Python expertise — consider hiring or training."
- ❌ Prohibited: Auto-assigning mandatory training based on analytics scores without employee consent.

---

## 2. Balanced Growth Framework

The framework tracks eight dimensions. Each dimension has explicit **what it measures**, **how it is bounded**, and **what it must not become**.

### Dimension 1: Contribution

| Aspect | Detail |
|--------|--------|
| What it tracks | Meaningful participation in team outcomes — code shipped, documents written, decisions supported, problems solved. |
| Signal source | Niyantran (tasking/execution telemetry), Sampada audit logs, voluntary self-reports. |
| Aggregation | Team-level and time-window aggregated. Individual raw counts are not exposed to managers by default. |
| Boundary | Must never become a productivity surveillance metric. No hourly or daily contribution monitoring. |

### Dimension 2: Learning

| Aspect | Detail |
|--------|--------|
| What it tracks | Modules completed, skills acquired, certifications earned, workshops attended. |
| Signal source | LXP integration (external), voluntary learning logs. |
| Aggregation | Individual progress visible to the individual; team completion rates visible to HR/manager in aggregate. |
| Boundary | Learning pace is not a performance metric. Slow learners are not penalised. |

### Dimension 3: Ownership Maturity

| Aspect | Detail |
|--------|--------|
| What it tracks | Progression from task-receiver to problem-owner — initiative, accountability, follow-through. |
| Signal source | Niyantran task closure signals, peer recognition signals (opt-in). |
| Aggregation | Qualitative trajectory view over quarters, not weekly snapshots. |
| Boundary | Ownership is context-dependent. Individuals going through personal challenges are excluded from maturity signals during declared wellbeing periods. |

### Dimension 4: Collaboration

| Aspect | Detail |
|--------|--------|
| What it tracks | Cross-team participation, knowledge sharing, pair-work signals. |
| Signal source | Voluntary collaboration logs, mentorship records, cross-team project participation. |
| Aggregation | Team-level visibility. Individual collaboration signals are self-reported or explicitly opted-in. |
| Boundary | Collaboration quality cannot be inferred from communication frequency alone. Social style differences (introverts vs extroverts) must be respected. |

### Dimension 5: Mentoring

| Aspect | Detail |
|--------|--------|
| What it tracks | Active mentoring relationships — sessions held, skills shared, mentee progress. |
| Signal source | Mentorship program records, voluntary session logs. |
| Aggregation | Shown as mentorship activity (sessions held, mentees active) — never as a ranking of mentors. |
| Boundary | Mentoring must remain voluntary. Forced mentoring with tracked KPIs violates this framework. |

### Dimension 6: Growth Trajectory

| Aspect | Detail |
|--------|--------|
| What it tracks | Direction and velocity of skill development over time — is the individual broadening, deepening, or pivoting? |
| Signal source | Skills mapping over quarterly intervals, learning completion, project complexity growth. |
| Aggregation | Individual view (personal growth map). Manager sees team-level trajectory heatmap. |
| Boundary | Trajectory is comparative only to the individual's past self — never to colleagues. |

### Dimension 7: Aspirations

| Aspect | Detail |
|--------|--------|
| What it tracks | Where the employee wants to go — stated career goals, role preferences, skill development wishes. |
| Signal source | Voluntary self-declaration in employee profile. Structured HR check-in inputs. |
| Aggregation | Strictly individual and confidential. Accessible only to the individual and their direct HR partner. |
| Boundary | Aspiration data must never be shared with clients, used in hiring decisions against the individual, or surfaced in team-level dashboards. |

### Dimension 8: Wellbeing Signals (Bounded)

| Aspect | Detail |
|--------|--------|
| What it tracks | General wellbeing indicators — leave patterns, workload signals, self-reported stress flags. |
| Signal source | HR request system, leave system, voluntary wellbeing check-ins. |
| Aggregation | Surfaced only as anonymised team-level flags ("team workload is elevated"). Individual wellbeing signals are private. |
| Boundary | **Strictest boundary**: No individual wellbeing data may be visible to managers without explicit written consent from the employee. No inference of mental health from work patterns. |

---

## 3. Anti-Patterns — Prohibited Implementations

The following patterns are explicitly **prohibited** within Sampada:

| Anti-Pattern | Why Prohibited | Alternative |
|---|---|---|
| Employee leaderboards | Converts growth into competition; creates coercive ranking pressure | Team momentum views (no individual ranking) |
| Dopamine loops (streaks, badges for output) | Manipulates intrinsic motivation; creates artificial engagement pressure | Milestone acknowledgement without streak mechanics |
| Productivity heat maps (individual, hourly) | Surveillance; penalises context-dependent productivity fluctuations | Quarterly contribution reviews with manager and employee |
| Composite "employee score" | Reduces human complexity to a single number; invites misuse | Multi-dimensional profile with no single score |
| Forced learning deadlines with penalty | Removes autonomy; creates anxiety-driven learning | Recommended learning with manager-employee goal-setting |
| Real-time activity monitoring | Violates psychological safety; creates observation anxiety | Outcome-based contribution tracking with appropriate intervals |
| Cross-employee skill comparison | Creates inadequacy feelings; ignores context | Individual growth trajectory vs own past baseline |

---

## 4. Data Privacy and Retention Guardrails

### 4.1 Data Minimisation
- Collect only the minimum signals required to support each growth dimension.
- Self-reported data (aspirations, wellbeing) is collected only with explicit opt-in.
- Inferred data (e.g., productivity inferred from commit frequency) is strictly prohibited unless the employee explicitly opts in.

### 4.2 Retention Rules
| Data Type | Retention Period | Who Can Access |
|---|---|---|
| Learning completion | Indefinite (employee's record) | Employee + HR |
| Contribution signals | 2 years rolling | Employee + Direct Manager (aggregate only) |
| Aspiration declarations | Until updated by employee | Employee + Assigned HR Partner |
| Wellbeing signals | 90 days (self-reported) | Employee only; anonymised team aggregates to HR |
| Mentorship logs | Indefinite | Mentor + Mentee + HR |

### 4.3 Access Control Matrix
| Role | Can See | Cannot See |
|---|---|---|
| Employee | Own full profile, trajectory, aspirations, wellbeing | Colleagues' individual data |
| Direct Manager | Team-level aggregates, own team's learning completion, flagged workload signals | Individual aspiration/wellbeing data |
| HR Partner | All aggregate signals, individual data with consent | Data the employee has explicitly restricted |
| Executive | Org-level aggregates only | Individual profiles, team-level detail |
| Sampada / SETU | Aggregated, anonymised signals | Any individual PII without explicit consent chain |

---

## 5. Implementation Recommendations

### 5.1 Frontend UX Guidance
- **No single score or rank** on any profile or dashboard view.
- **Personal growth map** (spider/radar chart showing own trajectory over time) — individual view only.
- **Team momentum panel** — aggregate completion rates, active mentorships, avg trajectory direction — no individual names.
- **Aspiration alignment indicator** — shows only whether the employee's current trajectory aligns with their stated goals (self-view only).
- **Wellbeing flag** — surfaces as an anonymised team-level indicator: "3 team members have flagged elevated workload this week." No individual attribution.

### 5.2 Backend API Design
- Growth endpoints must enforce role-based access at API level — not just UI level.
- Aspiration and wellbeing endpoints must require explicit employee consent token in every request.
- All growth analytics queries must aggregate before returning to manager-role callers.
- Audit every access to individual growth data (who accessed, when, for what purpose).

### 5.3 Consent Architecture
- Introduce a `GrowthConsent` model in MongoDB tracking:
  - `employee_id`
  - `dimension` (aspiration / wellbeing / collaboration)
  - `consent_granted` (boolean)
  - `consent_scope` (self | hr_partner | manager_aggregate)
  - `consent_timestamp`
  - `expires_at` (optional)
- Every access to dimension data checks consent before returning results.

### 5.4 Sample Metrics (Acceptable)
| Metric | Aggregation Level | Privacy Safe? |
|---|---|---|
| Team learning completion rate | Team aggregate | ✅ Yes |
| Mentorship sessions this quarter | Individual (self-view) | ✅ Yes |
| Skill trajectory direction (broadening/deepening) | Individual vs own baseline | ✅ Yes |
| Workload flag frequency | Team anonymised count | ✅ Yes |
| Hiring vs aspiration alignment | Individual (HR partner view with consent) | ✅ Yes (with consent) |
| Individual productivity score | Per-person | ❌ Prohibited |
| Hourly activity heatmap | Per-person | ❌ Prohibited |
| Peer ranking by contribution | Cross-person | ❌ Prohibited |

---

## 6. SETU Convergence Alignment

The Human Growth Model interacts with SETU-connected systems as follows:

| System | Interaction | Boundary |
|---|---|---|
| **Niyantran** | Provides task completion signals (opt-in, hashed employee IDs) for contribution dimension | Read-only; Sampada does not issue task directives |
| **Artha** | No direct interaction with growth data | Payroll signals are finance-owned; growth ≠ compensation authority |
| **CRM** | No interaction | Employee growth is internal; not exposed to client-facing CRM |
| **SETU Aggregator** | Receives anonymised team-level growth health signals for org-level workforce intelligence | Individual data never crosses to SETU without consent chain |

---

## 7. Healthy Ambition vs Manipulation — Enforcement

The system must actively distinguish and enforce:

| Signal Type | Healthy Ambition | Manipulation |
|---|---|---|
| Learning | "Here are skills trending in your target role" | "You must complete 5 modules or your score drops" |
| Growth trajectory | "Your trajectory aligns with senior engineer path" | "You are ranked 12th of 15 in growth this quarter" |
| Contribution | "Your team completed the sprint — great work" | "You contributed 8% less than average — improve" |
| Mentorship | "You have an active mentee — check in this week" | "Your mentoring count is 0 — this affects your review" |

**Implementation rule**: Any feature or metric that could be read as a threat, ranking, or coercive instruction must be redesigned or removed before shipping.

---

## 8. Open Items and Roadmap

| Item | Status | Owner |
|---|---|---|
| GrowthConsent model implementation | Planned | Backend team (under Rishabh direction) |
| LXP integration for learning signals | Planned | Integration team |
| Personal growth map UI component | Planned | Nikhil (Frontend) |
| Wellbeing check-in flow | Planned | HR + Product |
| Consent audit trail | Planned | Backend team |
| HR partner access controls | Planned | Backend team |

---

*This document is maintained by the Sampada Support Builder role. Changes to implementation direction or data architecture require Rishabh Yadav's approval.*
