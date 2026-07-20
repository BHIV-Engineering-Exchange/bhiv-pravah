# BHIV Design System — Layout Rules

## Overview
Layout conventions extracted from ARTHA's production dashboard pages. Following these rules ensures
visual consistency when a new BHIV product reuses dashboard patterns without copying ARTHA code.

---

## 1. Global Page Shell

Every ARTHA page lives inside a fixed chrome: sticky header + fixed sidebar + scrollable main content area.

```
┌────────────────────────────────────────────────────────────────────┐
│  HEADER (position: fixed; height: 72 px; z-index: 50)             │
│  Glassmorphism: backdrop-blur-xl; bg-background/80; border-bottom  │
├──────────────┬─────────────────────────────────────────────────────┤
│              │                                                     │
│  SIDEBAR     │  MAIN CONTENT                                       │
│  fixed       │  margin-left: 256 px                                │
│  width:256px │  padding-top: 72 px                                 │
│  height:     │  min-height: 100vh                                  │
│  calc(100vh  │                                                     │
│  - 72px)     │  ┌── container-main ─────────────────────────────┐  │
│              │  │  max-width: 1280 px; mx-auto; px-4; py-8      │  │
│              │  └────────────────────────────────────────────────┘  │
└──────────────┴─────────────────────────────────────────────────────┘
```

```css
/* Core shell classes (from index.css) */
.header-glass  { position: fixed; top: 0; left: 0; right: 0; height: 4.5rem; z-index: 50; }
.sidebar       { position: fixed; left: 0; width: 16rem; height: calc(100vh - 4.5rem); top: 4.5rem; }
.main-content  { margin-left: 16rem; padding-top: 4.5rem; min-height: 100vh; }
.container-main { max-width: 80rem; margin-inline: auto; padding-inline: 1rem; padding-block: 2rem; }
```

**Rule:** Always compose pages inside `.container-main` to maintain max-width and side padding.

---

## 2. Dashboard Page Skeleton

Every dashboard view uses a vertical stack of sections with consistent vertical rhythm.

```
<page>
  ├── Page Header Row           (title + CTA buttons)
  ├── KPI Card Grid             (4-col or 3-col)
  ├── Primary Chart Row         (2-col: main chart + secondary)
  ├── Secondary Data Row        (timeline, breakdown, distribution)
  └── Activity / Table Row      (recent records, action list)
```

```jsx
// ARTHA Dashboard skeleton (Dashboard.jsx pattern)
<div className="space-y-6 animate-fadeIn">   {/* 24 px section gaps */}
  <PageHeader />
  <KPIGrid />
  <ChartRow />
  <ActivityRow />
</div>
```

**Rule:** Use `space-y-6` (24 px) between major sections. Use `space-y-5` (20 px) in dense views (Signal dashboard).

---

## 3. Grid Patterns

### 3.1 — KPI Card Grid
```css
/* 4-across on desktop, 2-across tablet, 1-across mobile */
.bhiv-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}
@media (max-width: 1024px) { .bhiv-kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px)  { .bhiv-kpi-grid { grid-template-columns: 1fr; } }
```

**ARTHA source:** `Dashboard.jsx` — `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6`

### 3.2 — Chart Row (2-column)
```css
.bhiv-chart-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}
@media (max-width: 768px) { .bhiv-chart-row { grid-template-columns: 1fr; } }
```

### 3.3 — Signal Intelligence Layout (3-zone)
```css
/* Left: signal stack | Center: cost intelligence | Right: signal detail */
.bhiv-signal-layout {
  display: grid;
  grid-template-columns: 3fr 6fr 3fr;   /* 25% | 50% | 25% */
  gap: 1.25rem;
}
@media (max-width: 1280px) { .bhiv-signal-layout { grid-template-columns: 1fr; } }
```

**ARTHA source:** `FinancialIntelligenceDashboard.jsx` — `grid xl:grid-cols-12 gap-5`
_(col-span-3 | col-span-6 | col-span-3)_

### 3.4 — Compliance 3-Column
```css
.bhiv-compliance-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}
@media (max-width: 1024px) { .bhiv-compliance-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px)  { .bhiv-compliance-grid { grid-template-columns: 1fr; } }
```

### 3.5 — Form Layout (2-column field pairs)
```css
.bhiv-form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}
@media (max-width: 640px) { .bhiv-form-grid { grid-template-columns: 1fr; } }
```

---

## 4. Information Hierarchy Rules

### 4.1 — Section Priority Order
Every dashboard section must follow this scan order (top → bottom):

```
1. STATUS / ALERT BANNER  — Always top if present (RuntimeModeBanner, error cards)
2. KPI CARDS              — High-level numbers: the "at a glance" row
3. TREND CHARTS           — Time-series data: the "how did we get here" row
4. SIGNAL / ALERT LIST    — Active issues: the "what needs attention" row
5. ACTIVITY TABLE         — Recent records: the "what just happened" row
6. QUICK ACTIONS          — CTA row: role-gated, bottom of page
```

**Rule:** Never put Quick Actions above KPI cards. Never put charts above status banners.

### 4.2 — Card Hierarchy
Inside a single card, content must flow:
```
┌──────────────────────────────────────────┐
│  Card Title (font-semibold, lg)          │
│  Card Description (muted-foreground, sm) │
├──────────────────────────────────────────┤
│  Primary Metric (2xl–3xl, font-bold)     │
│  Secondary Metric (sm, muted)            │
│  Trend Indicator (icon + text, sm)       │
└──────────────────────────────────────────┘
```

### 4.3 — Severity Stacking
When displaying signals or alerts, always sort HIGH → MEDIUM → LOW top-to-bottom.
Never mix severity levels without visual grouping (heading or divider).

---

## 5. Responsive Breakpoints

| Name | Width | Layout behavior |
|------|-------|----------------|
| Mobile | < 640 px | Single column; sidebar hidden or drawer |
| Tablet | 640–1024 px | 2-column grids; sidebar collapsed |
| Desktop | 1024–1280 px | 3–4 column grids; sidebar expanded |
| Wide | ≥ 1280 px | Full signal intelligence 3-zone layout unlocked |

**Rule:** All grid patterns must degrade gracefully. Test every layout at 375 px (iPhone SE) and 768 px (iPad).

---

## 6. Z-Index Layers

```css
:root {
  --bhiv-z-base:      0;     /* Page content */
  --bhiv-z-raised:   10;     /* Hover cards, tooltips within flow */
  --bhiv-z-dropdown: 20;     /* Select dropdowns, date pickers */
  --bhiv-z-sticky:   30;     /* Sticky table headers */
  --bhiv-z-sidebar:  40;     /* Sidebar (fixed) */
  --bhiv-z-header:   50;     /* Top header (fixed) */
  --bhiv-z-modal:    60;     /* Modals and drawers */
  --bhiv-z-toast:    70;     /* Notification toasts */
  --bhiv-z-overlay:  80;     /* Full-screen overlays, loading screens */
}
```

---

## 7. Animation & Transition Rules

### Page Entry
```css
/* ARTHA uses animate-fadeIn on every dashboard root div */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn { animation: fadeIn 300ms ease-out; }
```

### Card Hover
```css
/* Subtle lift on hover — applied globally via .card:hover */
.bhiv-card:hover { transform: scale(1.01); transition: transform 300ms ease-out; }
```

### State Transitions
All interactive elements must use `transition-all duration-300` (300 ms, ease-out) for color, background, border, shadow changes.
Never use `transition: none` on visible interactive elements.

---

## 8. Sidebar Navigation Rules

```
SIDEBAR ANATOMY:
  ┌── Logo / Brand ──────────────────────────────┐  40 px height
  ├── Navigation Group: Core ────────────────────┤
  │   Dashboard                                  │  36 px item height
  │   Financial Intelligence                     │
  ├── Navigation Group: Financial ───────────────┤  8 px section gap + label
  │   Invoices  Expenses  Accounting             │
  ├── Navigation Group: Compliance ──────────────┤
  │   GST  TDS  Reports                          │
  ├── Navigation Group: Settings ────────────────┤
  │   Settings                                   │
  └── Theme Toggle ──────────────────────────────┘  bottom-pinned
```

**Rules:**
- Active item: background `bg-primary/10`, text `text-primary`, left border 3 px `border-primary`
- Hover item: background `bg-muted/50`, transition 200 ms
- Group labels: `text-xs uppercase tracking-wider text-muted-foreground font-semibold`
- Never mix icon-only and icon+label items in the same sidebar

---

## 9. Role-Gated Layout Rules

ARTHA gates layout sections by user role. New BHIV products should follow this pattern:

| Role | KPI Cards | Charts | Signals | Quick Actions | Settings |
|------|-----------|--------|---------|--------------|---------|
| admin | ✓ full | ✓ all | ✓ all | ✓ all | ✓ |
| accountant | ✓ full | ✓ all | ✓ all | ✓ (no user mgmt) | ✗ |
| viewer | ✓ read | ✓ read | ✗ hidden | ✗ (view reports only) | ✗ |

```jsx
// ARTHA pattern for role-gated sections
{(userRole === 'admin' || userRole === 'accountant') && (
  <QuickActions />
)}
```

---

## 10. Loading States

**Rule:** Every data section must handle 3 states: `loading`, `error`, `empty`, `populated`.

| State | Component | Pattern |
|-------|-----------|---------|
| Loading | `<Loading.Page />` or `<Loading size="md" />` | Full page spinner or card skeleton |
| Error | `<Card className="border-destructive/30 bg-destructive/5">` | Inline error with retry |
| Empty | `<EmptyState>` or custom empty component | Icon + message + CTA |
| Populated | Normal content render | Animate in with fadeIn |

---

**Design System Version**: 1.0  
**Last Updated**: June 2026  
**Source**: ARTHA dashboard codebase (Dashboard.jsx, FinancialIntelligenceDashboard.jsx)  
