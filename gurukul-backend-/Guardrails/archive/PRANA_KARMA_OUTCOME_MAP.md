# PRANA & Karma Outcome Map

## Purpose
Analyze and document the influence of PRANA observational states and Karma append-only records on system outcomes within the Gurukul/BHIV platform.

---

## 1. System Outcome Mapping

### 1.1 Progression
- **Karma Levels**
    - **Influencing Data**: DharmaPoints balance
    - **PRANA Involvement**: Indirect (via state mapping)
    - **Karma Involvement**: Direct (balance lookup)
    - **Linkage Type**: **Contaminated** (User-facing)
- **Daily Goal Status**
    - **Influencing Data**: Timer duration, manual stop
    - **PRANA Involvement**: Indirect (distraction detection)
    - **Karma Involvement**: Direct (penalty on stop)
    - **Linkage Type**: **Contaminated** (Enforcement)
- **Curriculum Unlocking**
    - **Influencing Data**: Completed Milestones
    - **PRANA Involvement**: None
    - **Karma Involvement**: None
    - **Linkage Type**: Observational-only
- **Achievement Badges**
    - **Influencing Data**: Streak days, quiz completion
    - **PRANA Involvement**: None
    - **Karma Involvement**: None
    - **Linkage Type**: Observational-only

### 1.2 Visibility
- **Student Dashboard**
    - **Influencing Data**: DharmaPoints, Levels
    - **PRANA Involvement**: Indirect (mapped to actions)
    - **Karma Involvement**: Direct (widget display)
    - **Linkage Type**: **Contaminated** (User-facing)
- **Real-time Toasts**
    - **Influencing Data**: Deltas in Karma balance
    - **PRANA Involvement**: Indirect (mapped to states)
    - **Karma Involvement**: Direct (context notification)
    - **Linkage Type**: **Contaminated** (Nudge)
- **Teacher Progress View**
    - **Influencing Data**: Aggregated activity data
    - **PRANA Involvement**: None
    - **Karma Involvement**: None (Placeholder only)
    - **Linkage Type**: Observational-only
- **Admin Analytics**
    - **Influencing Data**: Population-level trends
    - **PRANA Involvement**: None
    - **Karma Involvement**: Indirect (aggregated)
    - **Linkage Type**: Observational-only

### 1.3 Access
- **Role Assignment**
    - **Influencing Data**: Auth Role (admin, teacher)
    - **PRANA Involvement**: None
    - **Karma Involvement**: None
    - **Linkage Type**: Zero Involvement
- **Module Access**
    - **Influencing Data**: User subscription/enrollment
    - **PRANA Involvement**: None
    - **Karma Involvement**: None
    - **Linkage Type**: Zero Involvement

### 1.4 Notifications
- **Karmic Penalty Alert**
    - **Influencing Data**: Negative Karma events
    - **PRANA Involvement**: Indirect (Distraction state)
    - **Karma Involvement**: Direct (Trigger)
    - **Linkage Type**: **Contaminated** (Enforcement)
- **Achievement Toasts**
    - **Influencing Data**: Boolean flag triggers
    - **PRANA Involvement**: None
    - **Karma Involvement**: None
    - **Linkage Type**: Zero Involvement

### 1.5 Reviews
- **Reflection Cycle**
    - **Influencing Data**: Manual user input
    - **PRANA Involvement**: None
    - **Karma Involvement**: None (Logs only)
    - **Linkage Type**: Zero Involvement
- **Teacher Grading**
    - **Influencing Data**: Quiz scores
    - **PRANA Involvement**: None
    - **Karma Involvement**: None
    - **Linkage Type**: Zero Involvement

---

## 2. Summary of Involvement

### 2.1 Outcomes with Zero PRANA/Karma Involvement
- **Role-based Access Control (RBAC)**: Managed strictly by AuthContext and PostgreSQL user roles.
- **Teacher Grading**: Based on objective quiz performance in `quiz.py`.
- **Enrollment Access**: Managed by `ems.py` sync logic.

### 2.2 Outcomes with Observational-Only Linkage
- **Admin Analytics**: `ReportsAnalytics.jsx` utilizes aggregated user growth and activity counts, but does not identify individuals or influence outcomes for them.
- **Learning Flow**: `journey.py` utilizes heuristic-based progress (checks for summaries/reflections) but does not pull from Karma records currently.

### 2.3 Identification of Contamination (Out-of-Scope Influence)
- **Student Performance Nudges**: The `KarmaNotification` system provides immediate moralizing feedback ("Penalty applied. Reflect and realign") based on PRANA-derived states. This constitutes a feedback loop and outcome-influencing behavior.
- **Categorization Exposure**: The `KarmaWidget` exposes "Karma Levels" (Expert, Master, etc.), which creates a social/psychological outcome and potential optimization behavior by the user.
