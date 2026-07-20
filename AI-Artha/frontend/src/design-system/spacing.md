# BHIV Design System — Spacing

## Overview
Systematic spacing scale extracted from ARTHA dashboard implementation. Every margin, padding, and gap value
in ARTHA traces back to these tokens. Other BHIV products should import and use these — never hardcode pixel values.

## Philosophy
- **8-point grid** — base unit is 4 px; all spacing is a multiple of 4  
- **Contextual scale** — component density, page density, and chart density each have explicit guidance  
- **Responsive** — spacing contracts on mobile using responsive variants  
- **Predictable** — the same token always produces the same visual result across products

---

## Spacing Scale (CSS Custom Properties)

```css
:root {
  /* ── Core Scale (4 px base) ── */
  --bhiv-space-0:   0;
  --bhiv-space-px:  1px;
  --bhiv-space-0_5: 0.125rem;   /*  2 px */
  --bhiv-space-1:   0.25rem;    /*  4 px */
  --bhiv-space-1_5: 0.375rem;   /*  6 px */
  --bhiv-space-2:   0.5rem;     /*  8 px */
  --bhiv-space-2_5: 0.625rem;   /* 10 px */
  --bhiv-space-3:   0.75rem;    /* 12 px */
  --bhiv-space-3_5: 0.875rem;   /* 14 px */
  --bhiv-space-4:   1rem;       /* 16 px */
  --bhiv-space-5:   1.25rem;    /* 20 px */
  --bhiv-space-6:   1.5rem;     /* 24 px */
  --bhiv-space-7:   1.75rem;    /* 28 px */
  --bhiv-space-8:   2rem;       /* 32 px */
  --bhiv-space-9:   2.25rem;    /* 36 px */
  --bhiv-space-10:  2.5rem;     /* 40 px */
  --bhiv-space-12:  3rem;       /* 48 px */
  --bhiv-space-14:  3.5rem;     /* 56 px */
  --bhiv-space-16:  4rem;       /* 64 px */
  --bhiv-space-20:  5rem;       /* 80 px */
  --bhiv-space-24:  6rem;       /* 96 px */
  --bhiv-space-32:  8rem;       /* 128 px */
}
```

---

## Semantic Spacing Tokens

Map semantic intent to scale values so components express *why*, not *how many pixels*.

```css
:root {
  /* ── Component Internal Spacing ── */
  --bhiv-padding-xs:   var(--bhiv-space-1);    /*  4 px — icon chips, micro badges */
  --bhiv-padding-sm:   var(--bhiv-space-2);    /*  8 px — compact badges, tight labels */
  --bhiv-padding-md:   var(--bhiv-space-4);    /* 16 px — standard button, input */
  --bhiv-padding-lg:   var(--bhiv-space-6);    /* 24 px — card body default */
  --bhiv-padding-xl:   var(--bhiv-space-8);    /* 32 px — section containers */
  --bhiv-padding-2xl:  var(--bhiv-space-12);   /* 48 px — page-level padding */

  /* ── Gap / Grid Spacing ── */
  --bhiv-gap-xs:   var(--bhiv-space-1);    /*  4 px — icon + label */
  --bhiv-gap-sm:   var(--bhiv-space-2);    /*  8 px — badge row, icon row */
  --bhiv-gap-md:   var(--bhiv-space-4);    /* 16 px — form field stack */
  --bhiv-gap-lg:   var(--bhiv-space-6);    /* 24 px — dashboard card grid */
  --bhiv-gap-xl:   var(--bhiv-space-8);    /* 32 px — section-to-section */

  /* ── Border Radius ── */
  --bhiv-radius-sm:   0.375rem;   /*  6 px — badges, chips */
  --bhiv-radius-md:   0.75rem;    /* 12 px — inputs, small cards */
  --bhiv-radius-lg:   1rem;       /* 16 px — standard cards */
  --bhiv-radius-xl:   1.25rem;    /* 20 px — large panels */
  --bhiv-radius-2xl:  1.5rem;     /* 24 px — modals, overlays */
  --bhiv-radius-full: 9999px;     /* pill buttons, avatar rings */
}
```

---

## Layout Dimensions

```css
:root {
  /* ── Sidebar ── */
  --bhiv-sidebar-width:      16rem;   /* 256 px — standard sidebar */
  --bhiv-sidebar-width-collapsed: 4rem; /* 64 px — icon-only mode */

  /* ── Top Header ── */
  --bhiv-header-height: 4.5rem;   /* 72 px — sticky top bar */

  /* ── Main Content ── */
  --bhiv-content-max-width: 80rem;   /* 1280 px — max page width */
  --bhiv-content-padding-x: var(--bhiv-space-4);   /* 16 px mobile */
  --bhiv-content-padding-y: var(--bhiv-space-8);   /* 32 px mobile */

  /* ── Modal ── */
  --bhiv-modal-sm:  24rem;   /* 384 px */
  --bhiv-modal-md:  32rem;   /* 512 px */
  --bhiv-modal-lg:  42rem;   /* 672 px */
  --bhiv-modal-xl:  56rem;   /* 896 px */
}
```

---

## Dashboard Card Anatomy

Every ARTHA dashboard card uses a consistent internal spacing contract.

```
┌─────────────────────────────────────────────────────────────┐
│ CARD (border-radius: --bhiv-radius-2xl; border: 1px)        │
│                                                             │
│  ┌── Card Header ───────────────────────────────────────┐  │
│  │  padding: 1.5rem (--bhiv-padding-lg) top/left/right  │  │
│  │  padding-bottom: 1rem  •  border-bottom: 1px         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌── Card Body ─────────────────────────────────────────┐  │
│  │  padding: 1.5rem (--bhiv-padding-lg)                 │  │
│  │  gap between internal rows: --bhiv-gap-md (16 px)    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌── Card Footer ───────────────────────────────────────┐  │
│  │  padding: 1rem 1.5rem  •  border-top: 1px            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

```css
/* ARTHA Card spacing implementation */
.bhiv-card { padding: var(--bhiv-padding-lg); border-radius: var(--bhiv-radius-2xl); }
.bhiv-card-header { padding: var(--bhiv-padding-lg); padding-bottom: var(--bhiv-space-4); border-bottom: 1px solid; }
.bhiv-card-body  { padding: var(--bhiv-padding-lg); }
.bhiv-card-footer { padding: var(--bhiv-space-4) var(--bhiv-padding-lg); border-top: 1px solid; }
```

---

## Dashboard Grid Patterns

### 4-Column KPI Row (Executive / Main Dashboard)
```css
.bhiv-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--bhiv-gap-lg);   /* 24 px */
}
@media (max-width: 1024px) { .bhiv-kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px)  { .bhiv-kpi-grid { grid-template-columns: 1fr; } }
```

### 3-Column Signal Dashboard
```css
/* Used in: FinancialIntelligenceDashboard */
.bhiv-signal-grid {
  display: grid;
  grid-template-columns: 3fr 6fr 3fr;   /* 25% | 50% | 25% */
  gap: var(--bhiv-gap-lg);
}
@media (max-width: 1280px) { .bhiv-signal-grid { grid-template-columns: 1fr; } }
```

### 2-Column Chart Grid
```css
.bhiv-chart-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--bhiv-gap-lg);
}
@media (max-width: 768px) { .bhiv-chart-grid { grid-template-columns: 1fr; } }
```

### Full-Width Timeline
```css
.bhiv-timeline-row { display: grid; grid-template-columns: 1fr; gap: var(--bhiv-gap-lg); }
```

---

## Component Density Guidelines

| Density | Context | Padding | Gap | Use When |
|---------|---------|---------|-----|----------|
| **Compact** | Data tables, timeline rows, signal chips | 8 px | 8 px | Many items need to scan vertically |
| **Default** | KPI cards, form sections, modal content | 16–24 px | 16 px | Standard dashboard view |
| **Comfortable** | Executive summaries, alert panels | 24–32 px | 24 px | High-importance, low-density information |
| **Spacious** | Landing overlays, empty states | 32–48 px | 32 px | No content pressure, breathe room |

---

## Section Spacing

Space between major dashboard sections:

```css
/* Standard inter-section gap (used in Dashboard.jsx and FinancialIntelligenceDashboard.jsx) */
.bhiv-dashboard-stack { display: flex; flex-direction: column; gap: var(--bhiv-gap-xl); }   /* 32 px */

/* Tight section stack — compliance panels, signal detail */
.bhiv-section-tight  { display: flex; flex-direction: column; gap: var(--bhiv-gap-lg); }    /* 24 px */

/* Page top-level layout wrapper */
.bhiv-page-container {
  max-width: var(--bhiv-content-max-width);
  margin-inline: auto;
  padding-inline: var(--bhiv-content-padding-x);
  padding-block: var(--bhiv-content-padding-y);
}
```

---

## Tailwind Mapping (ARTHA uses Tailwind)

ARTHA uses Tailwind utility classes. This table maps BHIV tokens to equivalent Tailwind classes for adoption in Tailwind-based BHIV products.

| BHIV Token | Tailwind Class | Pixels |
|------------|---------------|--------|
| `--bhiv-space-2` | `p-2`, `m-2`, `gap-2` | 8 px |
| `--bhiv-space-4` | `p-4`, `m-4`, `gap-4` | 16 px |
| `--bhiv-space-6` | `p-6`, `m-6`, `gap-6` | 24 px |
| `--bhiv-space-8` | `p-8`, `m-8`, `gap-8` | 32 px |
| `--bhiv-gap-lg` | `gap-6` | 24 px — card grid |
| `--bhiv-radius-2xl` | `rounded-2xl` | 24 px — cards |
| `--bhiv-radius-xl` | `rounded-xl` | 20 px — buttons/inputs |

---

## React Usage Pattern

```jsx
// Recommended: consume tokens via CSS custom properties
const DashboardSection = ({ children }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--bhiv-gap-xl)' }}>
    {children}
  </div>
);

// Or with Tailwind (ARTHA pattern)
const DashboardSection = ({ children }) => (
  <div className="space-y-8">{children}</div>
);
```

---

## Extension Notes

When extending spacing for a new BHIV product:
1. **Never introduce raw pixel values** — add a new semantic token if needed
2. **Always document density intent** — state whether a new spacing is Compact / Default / Comfortable
3. **Maintain the 4-point grid** — all new values must be multiples of 4 px
4. **Mobile-first** — define the default for small screens, override up for `md:` and `lg:`

---

**Design System Version**: 1.0  
**Grid Base**: 4 px  
**Breakpoints**: `sm` 640 px · `md` 768 px · `lg` 1024 px · `xl` 1280 px  
**Last Updated**: June 2026  
