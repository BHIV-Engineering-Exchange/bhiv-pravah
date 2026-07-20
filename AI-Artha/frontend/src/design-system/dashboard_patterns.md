# BHIV Design System — Dashboard Patterns

## Overview
Documented dashboard layout patterns from ARTHA. Use this as the reference when building new BHIV
product dashboards. Each pattern includes layout rules, information hierarchy, density guidance,
and scanability guidance.

---

## Pattern 1 — Executive Dashboard

**Purpose:** High-level financial health overview for executives and administrators.  
**ARTHA Source:** `frontend/src/pages/dashboard/Dashboard.jsx`  
**URL Path:** `/dashboard`  
**Required Roles:** All (content gated by role)

### Layout Blueprint
```
┌────────────────────────────────────────────────────────────────────────┐
│  PAGE HEADER                                                           │
│  "Welcome, {name}!" · subtitle · [New Invoice] [New Expense] CTAs     │
├────────────────────────────────────────────────────────────────────────┤
│  KPI ROW — 4 columns (lg:grid-cols-4 md:grid-cols-2)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│  │Total     │ │Total     │ │Pending   │ │Outstdng  │                 │
│  │Revenue   │ │Expenses  │ │Invoices  │ │Amount    │                 │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                 │
├──────────────────────────────┬─────────────────────────────────────────┤
│  CHART — Revenue vs Expenses │  (currently single chart, expandable)   │
│  BarChart (monthly)          │                                         │
├──────────────────────────────┴─────────────────────────────────────────┤
│  TIMELINE CHART — Bank Transaction Timeline (full width)               │
│  AreaChart (daily credits/debits)                                      │
├──────────────────────────────┬─────────────────────────────────────────┤
│  Expense Breakdown PieChart  │                                         │
│  (by category)               │                                         │
├──────────────────────────────┴─────────────────────────────────────────┤
│  ACTIVITY ROW — 2 columns                                              │
│  ┌──────────────────────────┐  ┌──────────────────────────┐            │
│  │ Recent Invoices          │  │ Recent Expenses          │            │
│  │ (paginated list + badge) │  │ (paginated list + badge) │            │
│  └──────────────────────────┘  └──────────────────────────┘            │
├────────────────────────────────────────────────────────────────────────┤
│  QUICK ACTIONS (admin/accountant only) — 4 buttons in a row           │
│  [Create Invoice] [Add Expense] [Journal Entry] [View Reports]         │
└────────────────────────────────────────────────────────────────────────┘
```

### Information Hierarchy
1. **Identity** — who is the user, what role do they have
2. **Financial pulse** — KPI numbers (revenue, expenses, pending, outstanding)
3. **Trend context** — charts showing how numbers evolved
4. **Risk exposure** — outstanding amounts and pending invoices
5. **Operational feed** — recent records for quick navigation
6. **Action layer** — role-gated CTAs at the bottom

### Density Guidance
- **KPI Cards:** Default density — 24 px padding, large number (2xl font-bold), small label (sm muted)
- **Charts:** 300 px fixed height; responsive container fills card width
- **Activity Lists:** Compact density — 16 px vertical padding per row; dividers between rows
- **Quick Actions:** Comfortable — 16 px padding; icon 8×8, label 14 px

### Scanability Guidance
- KPI row must be **fully visible above the fold** on 1280 px desktop
- Each KPI card shows: label → value → trend (top-to-bottom)
- Status badges in activity lists use semantic colors (green=paid, amber=pending, red=overdue)
- Charts use stable color assignment: green=revenue/credits, red=expenses/debits

---

## Pattern 2 — Signal Intelligence Dashboard

**Purpose:** Real-time compliance signals with drill-down analysis for finance ops.  
**ARTHA Source:** `frontend/src/pages/dashboard/FinancialIntelligenceDashboard.jsx`  
**URL Path:** `/financial-intelligence`  
**Required Roles:** admin, accountant

### Layout Blueprint
```
┌────────────────────────────────────────────────────────────────────────┐
│  RUNTIME MODE BANNER (always visible)                                  │
│  Shows: CONNECTED | DEGRADED | UNAVAILABLE | MOCK                      │
├────────────────────────────────────────────────────────────────────────┤
│  ERROR SURFACE (conditional)                                           │
│  If signal fetch failed: inline error card with URL + status           │
├───────────────┬────────────────────────────────────────────────────────┤
│               │  KPI ROW — 3 columns                                   │
│               │  ┌─────────┐ ┌─────────┐ ┌─────────┐                  │
│               │  │Financial│ │Budget   │ │Active   │                  │
│               │  │Health   │ │Risk     │ │Issues   │                  │
│               │  └─────────┘ └─────────┘ └─────────┘                  │
├───────────────┼────────────────────────────┬───────────────────────────┤
│  SIGNAL STACK │  COST INTELLIGENCE VIEW    │  SIGNAL DETAIL ENGINE    │
│  (25% width)  │  (50% width)               │  (25% width)             │
│               │                            │                          │
│  Signal groups│  Planned / Actual / Variance│  Selected signal detail │
│  HIGH → LOW   │  Trend indicator            │  Trace ID               │
│  Per-signal   │  Department variance bars   │  Recommendation         │
│  severity     │                            │  SETU pipeline check     │
│  chips        │  COMPLIANCE VISIBILITY     │                          │
│               │  GST + TDS panels          │                          │
└───────────────┴────────────────────────────┴───────────────────────────┘
```

### Information Hierarchy
1. **System health** — runtime mode banner (is the backend connected?)
2. **Financial health score** — computed metric (0–100) from signal penalties
3. **Risk level** — HIGH / MEDIUM / LOW with severity badge
4. **Active issues count** — number of non-LOW signals
5. **Signal breakdown** — per-signal detail with drill-down
6. **Cost intelligence** — budget vs actual with variance bars
7. **Compliance layers** — GST and TDS status panels

### Density Guidance
- **Runtime Banner:** Compact — full width, 48 px height, muted or colored background
- **KPI Row:** Default — 3 cards, 16 px padding, smaller numbers than Executive dashboard
- **Signal Stack:** Compact — small chips, 12 px vertical padding, grouped by severity
- **Cost Intelligence:** Default — 12 px internal sub-card padding; progress bars 8 px height
- **Signal Detail:** Comfortable — right panel, 16–20 px padding, monospace trace IDs

### Scanability Guidance
- Signal stack always sorted: CRITICAL → HIGH → MEDIUM → LOW
- Severity uses color coding: red=CRITICAL/HIGH, amber=MEDIUM, green=LOW
- Selected signal highlighted with primary border
- Cost intelligence variance: red bar = over budget, green bar = under budget
- Runtime banner must be top-of-page — never hidden or scrolled away

---

## Pattern 3 — Compliance Dashboard (GST)

**Purpose:** GST filing status, period selection, GSTR-1/3B breakdown.  
**ARTHA Source:** `frontend/src/pages/compliance/GSTDashboard.jsx`  
**URL Path:** `/compliance/gst`  
**Required Roles:** admin, accountant

### Layout Blueprint
```
┌────────────────────────────────────────────────────────────────────────┐
│  PAGE HEADER + Period Selector                                         │
│  [GSTR-1] [GSTR-3B] tabs · Month/Year picker · [Generate] CTA        │
├────────────────────────────────────────────────────────────────────────┤
│  SUMMARY CARDS — 3 or 4 columns                                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│  │Output    │ │Input     │ │Net GST   │ │Filing    │                 │
│  │CGST+SGST │ │ITC       │ │Liability │ │Status    │                 │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                 │
├────────────────────────────────────────────────────────────────────────┤
│  INVOICE TABLE — Full width                                            │
│  Columns: Invoice# | Customer | Date | Taxable | CGST | SGST | Total  │
│  Rows: sortable, filterable, paginated                                 │
├────────────────────────────────────────────────────────────────────────┤
│  VALIDATION RESULTS (conditional)                                      │
│  If filing_ready=false: error list with signal links                   │
│  If filing_ready=true: green confirmation banner                       │
└────────────────────────────────────────────────────────────────────────┘
```

### Information Hierarchy
1. **Period context** — what filing period is this for?
2. **Aggregate liability** — output tax, ITC, net payable
3. **Filing readiness** — is this ready to submit?
4. **Transaction detail** — line-by-line invoice breakdown
5. **Validation errors** — what must be fixed before filing

### Density Guidance
- Summary cards: Default density — matches KPI cards
- Table: Compact — 12 px row padding; fixed column widths for currency alignment
- Validation errors: Comfortable — 16 px padding, each error as a distinct row

### Scanability Guidance
- Period selector prominently placed — always visible in header
- Filing status as a distinct badge (color-coded)
- Currency columns always right-aligned with monospace font
- Error rows sorted by severity; links to source invoice/signal

---

## Pattern 4 — Operations Dashboard

**Purpose:** Expense management, approval workflow, category breakdown.  
**ARTHA Source:** `frontend/src/pages/expenses/` pages  
**URL Path:** `/expenses`  
**Required Roles:** admin, accountant (write); viewer (read)

### Layout Blueprint
```
┌────────────────────────────────────────────────────────────────────────┐
│  PAGE HEADER + [New Expense] CTA (role-gated)                         │
├──────────────┬──────────────┬──────────────┬───────────────────────────┤
│ Total Spend  │ Approved     │ Pending      │ MTD vs Last Month         │
│ (YTD)        │ (count+amt)  │ (count+amt)  │ (trend indicator)         │
├──────────────┴──────────────┴──────────────┴───────────────────────────┤
│  FILTER ROW — Status | Category | Date Range | Search                  │
├────────────────────────────────────────────────────────────────────────┤
│  EXPENSE TABLE — Sortable, paginated                                   │
│  Columns: Date | Description | Category | Amount | Status | Actions    │
├────────────────────────────────────────────────────────────────────────┤
│  EXPENSE BREAKDOWN CHART (optional)                                    │
│  PieChart or BarChart by category                                      │
└────────────────────────────────────────────────────────────────────────┘
```

### Information Hierarchy
1. **Spend totals** — YTD, approved, pending (the "budget health" row)
2. **Filters** — narrow the visible data before the table renders
3. **Transaction table** — sortable, with status and action columns
4. **Category breakdown** — chart for visual distribution

### Density Guidance
- KPI row: Default — 4 cards
- Filter row: Compact — 40 px input height; inline layout
- Table: Compact — 12–16 px row padding
- Chart: Optional — 200–250 px height

---

## Pattern 5 — Observability Dashboard

**Purpose:** Trace reconstruction, signal pipeline status, ledger hash-chain health.  
**ARTHA Source:** Signal dashboard, trace endpoints  
**URL Path:** `/compliance/signals`  
**Required Roles:** admin, accountant

### Layout Blueprint
```
┌────────────────────────────────────────────────────────────────────────┐
│  OBSERVABILITY HEADER                                                  │
│  "Signal Trace Explorer" · [Evaluate Overdue Invoices] CTA            │
├───────────────────────┬───────────────────────┬────────────────────────┤
│  SIGNAL LIST          │  TRACE DETAIL         │  PIPELINE CHECK        │
│  (filter by type,     │  5-step trace chain:  │  Validation results:   │
│   severity)           │  Signal → Compliance  │  normalizer output     │
│                       │  → Filing → Journal   │  validator errors      │
│  Each row:            │  → Ledger             │  SETU payload preview  │
│  - type badge         │                       │                        │
│  - severity chip      │  Step markers:        │                        │
│  - timestamp          │  ✓ found / ✗ missing  │                        │
│  - trace_id (mono)    │  Expandable data      │                        │
└───────────────────────┴───────────────────────┴────────────────────────┘
```

### Information Hierarchy
1. **Signal inventory** — list of all active signals, sorted by severity
2. **Trace chain** — drill into a specific signal's 5-step lineage
3. **Pipeline validation** — can this signal be dispatched to SETU?

### Density Guidance
- Signal list: Compact — small row height, monospace trace IDs, colored severity chips
- Trace chain: Default — each step as a card with expand/collapse
- Pipeline check: Comfortable — JSON preview in monospace, error list

### Scanability Guidance
- Monospace font for all trace IDs (`font-mono`)
- Step chain uses connecting vertical line (border-l with dots)
- `✓` / `✗` indicators on each step
- Pipeline errors highlighted red; warnings amber; passing items green

---

## Cross-Pattern Rules

### Density Decision Tree
```
Is this an executive-facing view?
  Yes → Comfortable density (24–32 px padding, large numbers)
  No → Is this a data-dense table/list?
    Yes → Compact density (8–12 px padding, smaller text)
    No → Default density (16–24 px padding)
```

### Color Coding (consistent across all patterns)
| Signal | Color | Tailwind |
|--------|-------|---------|
| Revenue / Credit / Positive | Green | `text-success`, `bg-success/10` |
| Expense / Debit / Negative | Red | `text-destructive`, `bg-destructive/10` |
| Pending / Warning | Amber | `text-warning`, `bg-warning/10` |
| Informational | Blue | `text-info`, `bg-info/10` |
| Neutral / Secondary | Muted Gray | `text-muted-foreground` |

### Empty State Rule
Every list/table section must render an empty state component when data length = 0.
Never render an empty `<div>` or a `<table>` with zero rows without messaging.

```jsx
{data.length === 0 ? (
  <EmptyState icon={<IconName />} title="No records" message="Description." cta="Create first record" />
) : (
  <DataList items={data} />
)}
```

### Loading State Rule
Every async section must render a skeleton or spinner while data is fetching.
Never show a layout with missing content — the user must know data is loading.

---

**Design System Version**: 1.0  
**Last Updated**: June 2026  
**Source**: ARTHA dashboard codebase (Dashboard.jsx, FinancialIntelligenceDashboard.jsx, GSTDashboard.jsx)  
