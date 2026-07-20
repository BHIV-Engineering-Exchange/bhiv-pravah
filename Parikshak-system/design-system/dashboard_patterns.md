# BHIV Command Center Design System — Dashboard Patterns

Cognitive efficiency is the main driver of dashboard layouts. A reviewer or manager must grasp state, scores, and risks within 3–5 seconds.

## Cognition Flow Patterns

### 1. The 3-5 Seconds Rule
- Top-level statuses must be represented by prominent status badges using color gradients:
  - Green for PASS / READY.
  - Rose for FAIL / DANGER.
  - Amber for BORDERLINE / WARNING.
- The grading score must use huge typography (e.g. `text-6xl`) placed in the upper-left hot zone.

### 2. High Info-Density / Low Noise
- Replace generic text descriptors with compact, interactive metadata cards.
- Group metrics in logical lists (e.g. "Workloads", "Skills Match %").
- Use progress bars and gauges rather than raw numeric percentages where possible.

### 3. Traceability Over Decoration
- Every metric or decision block should have a visible trace ID or evidence link.
- Include a quick copy button for trace hashes.
- Embed evidence status indicators (e.g., "VERIFIED", "AUDITED").
