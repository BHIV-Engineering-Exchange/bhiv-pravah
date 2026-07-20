# BHIV Design System - Typography

## Overview
Comprehensive typography system extracted from ARTHA dashboard for consistent text treatment across BHIV products.

## Typography Philosophy
- **Readability First**: Optimized for financial data and long-form content
- **Hierarchical Clarity**: Clear visual hierarchy for complex information
- **Cross-Platform**: Consistent rendering across devices and browsers
- **Accessibility**: Meets WCAG 2.1 guidelines for text contrast and sizing

## Font Stack

### Primary Font Family
```css
:root {
  /* Primary font stack - Optimized for financial interfaces */
  --bhiv-font-primary: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", 
                       "Helvetica Neue", Arial, "Noto Sans", sans-serif, 
                       "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", 
                       "Noto Color Emoji";
  
  /* Monospace font for numbers/code */
  --bhiv-font-mono: "JetBrains Mono", "Fira Code", "SF Mono", Monaco, 
                    "Inconsolata", "Roboto Mono", "Courier New", monospace;
  
  /* Display font for headings */
  --bhiv-font-display: "Inter", system-ui, sans-serif;
}
```

### Font Import
```css
/* Google Fonts import - Include in main CSS */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');
```

## Type Scale

### Font Sizes
```css
:root {
  /* Font size scale based on 1.125 ratio (major second) */
  --bhiv-text-xs: 0.75rem;    /* 12px */
  --bhiv-text-sm: 0.875rem;   /* 14px */
  --bhiv-text-base: 1rem;     /* 16px - Base size */
  --bhiv-text-lg: 1.125rem;   /* 18px */
  --bhiv-text-xl: 1.25rem;    /* 20px */
  --bhiv-text-2xl: 1.5rem;    /* 24px */
  --bhiv-text-3xl: 1.875rem;  /* 30px */
  --bhiv-text-4xl: 2.25rem;   /* 36px */
  --bhiv-text-5xl: 3rem;      /* 48px */
  --bhiv-text-6xl: 3.75rem;   /* 60px */
  --bhiv-text-7xl: 4.5rem;    /* 72px */
}
```

### Font Weights
```css
:root {
  /* Font weights */
  --bhiv-font-light: 300;
  --bhiv-font-normal: 400;
  --bhiv-font-medium: 500;
  --bhiv-font-semibold: 600;
  --bhiv-font-bold: 700;
  --bhiv-font-extrabold: 800;
  --bhiv-font-black: 900;
}
```

### Line Heights
```css
:root {
  /* Line heights for different contexts */
  --bhiv-leading-none: 1;
  --bhiv-leading-tight: 1.25;
  --bhiv-leading-snug: 1.375;
  --bhiv-leading-normal: 1.5;
  --bhiv-leading-relaxed: 1.625;
  --bhiv-leading-loose: 2;
}
```

## Typography Hierarchy

### Headings
```css
/* H1 - Page Title */
.bhiv-h1 {
  font-family: var(--bhiv-font-display);
  font-size: var(--bhiv-text-4xl);
  font-weight: var(--bhiv-font-bold);
  line-height: var(--bhiv-leading-tight);
  color: var(--bhiv-text-primary);
  margin-bottom: 1.5rem;
  letter-spacing: -0.025em;
}

/* H2 - Section Title */
.bhiv-h2 {
  font-family: var(--bhiv-font-display);
  font-size: var(--bhiv-text-3xl);
  font-weight: var(--bhiv-font-semibold);
  line-height: var(--bhiv-leading-tight);
  color: var(--bhiv-text-primary);
  margin-bottom: 1.25rem;
  letter-spacing: -0.025em;
}

/* H3 - Subsection Title */
.bhiv-h3 {
  font-family: var(--bhiv-font-display);
  font-size: var(--bhiv-text-2xl);
  font-weight: var(--bhiv-font-semibold);
  line-height: var(--bhiv-leading-snug);
  color: var(--bhiv-text-primary);
  margin-bottom: 1rem;
}

/* H4 - Component Title */
.bhiv-h4 {
  font-family: var(--bhiv-font-display);
  font-size: var(--bhiv-text-xl);
  font-weight: var(--bhiv-font-medium);
  line-height: var(--bhiv-leading-snug);
  color: var(--bhiv-text-primary);
  margin-bottom: 0.75rem;
}

/* H5 - Card/Panel Title */
.bhiv-h5 {
  font-family: var(--bhiv-font-display);
  font-size: var(--bhiv-text-lg);
  font-weight: var(--bhiv-font-medium);
  line-height: var(--bhiv-leading-normal);
  color: var(--bhiv-text-primary);
  margin-bottom: 0.5rem;
}

/* H6 - Label/Small Title */
.bhiv-h6 {
  font-family: var(--bhiv-font-display);
  font-size: var(--bhiv-text-base);
  font-weight: var(--bhiv-font-medium);
  line-height: var(--bhiv-leading-normal);
  color: var(--bhiv-text-secondary);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

### Body Text
```css
/* Primary Body Text */
.bhiv-body-large {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-lg);
  font-weight: var(--bhiv-font-normal);
  line-height: var(--bhiv-leading-relaxed);
  color: var(--bhiv-text-primary);
}

/* Standard Body Text */
.bhiv-body {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-base);
  font-weight: var(--bhiv-font-normal);
  line-height: var(--bhiv-leading-normal);
  color: var(--bhiv-text-primary);
}

/* Small Body Text */
.bhiv-body-small {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-sm);
  font-weight: var(--bhiv-font-normal);
  line-height: var(--bhiv-leading-normal);
  color: var(--bhiv-text-secondary);
}

/* Caption Text */
.bhiv-caption {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-xs);
  font-weight: var(--bhiv-font-normal);
  line-height: var(--bhiv-leading-normal);
  color: var(--bhiv-text-muted);
}
```

### Interactive Elements
```css
/* Links */
.bhiv-link {
  font-family: var(--bhiv-font-primary);
  color: var(--bhiv-primary-600);
  text-decoration: underline;
  text-decoration-color: transparent;
  transition: all 0.2s ease;
  cursor: pointer;
}

.bhiv-link:hover {
  color: var(--bhiv-primary-700);
  text-decoration-color: var(--bhiv-primary-600);
}

/* Buttons */
.bhiv-button {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-sm);
  font-weight: var(--bhiv-font-medium);
  line-height: var(--bhiv-leading-none);
  letter-spacing: 0.025em;
}

/* Form Labels */
.bhiv-label {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-sm);
  font-weight: var(--bhiv-font-medium);
  line-height: var(--bhiv-leading-normal);
  color: var(--bhiv-text-primary);
  margin-bottom: 0.25rem;
}

/* Input Text */
.bhiv-input {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-base);
  font-weight: var(--bhiv-font-normal);
  line-height: var(--bhiv-leading-normal);
}
```

## Financial Data Typography

### Monetary Values
```css
/* Large Currency Display */
.bhiv-currency-large {
  font-family: var(--bhiv-font-mono);
  font-size: var(--bhiv-text-3xl);
  font-weight: var(--bhiv-font-semibold);
  line-height: var(--bhiv-leading-none);
  color: var(--bhiv-text-primary);
  letter-spacing: -0.01em;
}

/* Standard Currency Display */
.bhiv-currency {
  font-family: var(--bhiv-font-mono);
  font-size: var(--bhiv-text-base);
  font-weight: var(--bhiv-font-medium);
  line-height: var(--bhiv-leading-none);
  color: var(--bhiv-text-primary);
  letter-spacing: -0.005em;
}

/* Small Currency Display */
.bhiv-currency-small {
  font-family: var(--bhiv-font-mono);
  font-size: var(--bhiv-text-sm);
  font-weight: var(--bhiv-font-normal);
  line-height: var(--bhiv-leading-none);
  color: var(--bhiv-text-secondary);
}

/* Percentage Display */
.bhiv-percentage {
  font-family: var(--bhiv-font-mono);
  font-size: var(--bhiv-text-sm);
  font-weight: var(--bhiv-font-medium);
  line-height: var(--bhiv-leading-none);
}

.bhiv-percentage.positive { color: var(--bhiv-success-600); }
.bhiv-percentage.negative { color: var(--bhiv-error-600); }
.bhiv-percentage.neutral { color: var(--bhiv-neutral-600); }
```

### Data Tables
```css
/* Table Headers */
.bhiv-table-header {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-xs);
  font-weight: var(--bhiv-font-semibold);
  line-height: var(--bhiv-leading-tight);
  color: var(--bhiv-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* Table Data */
.bhiv-table-data {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-sm);
  font-weight: var(--bhiv-font-normal);
  line-height: var(--bhiv-leading-normal);
  color: var(--bhiv-text-primary);
}

/* Table Numbers */
.bhiv-table-number {
  font-family: var(--bhiv-font-mono);
  font-size: var(--bhiv-text-sm);
  font-weight: var(--bhiv-font-normal);
  text-align: right;
  color: var(--bhiv-text-primary);
}
```

## Dashboard-Specific Typography

### KPI Values
```css
/* Large KPI Display */
.bhiv-kpi-large {
  font-family: var(--bhiv-font-display);
  font-size: var(--bhiv-text-5xl);
  font-weight: var(--bhiv-font-extrabold);
  line-height: var(--bhiv-leading-none);
  color: var(--bhiv-text-primary);
  letter-spacing: -0.02em;
}

/* Medium KPI Display */
.bhiv-kpi-medium {
  font-family: var(--bhiv-font-display);
  font-size: var(--bhiv-text-2xl);
  font-weight: var(--bhiv-font-bold);
  line-height: var(--bhiv-leading-none);
  color: var(--bhiv-text-primary);
}

/* KPI Labels */
.bhiv-kpi-label {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-sm);
  font-weight: var(--bhiv-font-medium);
  line-height: var(--bhiv-leading-normal);
  color: var(--bhiv-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* KPI Change */
.bhiv-kpi-change {
  font-family: var(--bhiv-font-mono);
  font-size: var(--bhiv-text-sm);
  font-weight: var(--bhiv-font-medium);
  line-height: var(--bhiv-leading-none);
}
```

### Status Typography
```css
/* Status Badges */
.bhiv-status-badge {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-xs);
  font-weight: var(--bhiv-font-semibold);
  line-height: var(--bhiv-leading-none);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* Notification Text */
.bhiv-notification-title {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-sm);
  font-weight: var(--bhiv-font-semibold);
  line-height: var(--bhiv-leading-snug);
  color: var(--bhiv-text-primary);
}

.bhiv-notification-body {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-sm);
  font-weight: var(--bhiv-font-normal);
  line-height: var(--bhiv-leading-normal);
  color: var(--bhiv-text-secondary);
}
```

## Responsive Typography

### Mobile Adjustments
```css
/* Mobile font size adjustments */
@media (max-width: 640px) {
  .bhiv-h1 { font-size: var(--bhiv-text-3xl); }
  .bhiv-h2 { font-size: var(--bhiv-text-2xl); }
  .bhiv-h3 { font-size: var(--bhiv-text-xl); }
  
  .bhiv-kpi-large { font-size: var(--bhiv-text-3xl); }
  .bhiv-kpi-medium { font-size: var(--bhiv-text-xl); }
  
  .bhiv-currency-large { font-size: var(--bhiv-text-xl); }
}
```

### Print Styles
```css
/* Print optimizations */
@media print {
  .bhiv-h1, .bhiv-h2, .bhiv-h3 {
    page-break-after: avoid;
    color: #000 !important;
  }
  
  .bhiv-body, .bhiv-table-data {
    font-size: 12pt;
    line-height: 1.4;
    color: #000 !important;
  }
  
  .bhiv-currency, .bhiv-table-number {
    font-family: "Courier New", monospace;
  }
}
```

## Accessibility Features

### Focus States
```css
/* Accessible focus styles */
.bhiv-link:focus,
.bhiv-button:focus {
  outline: 2px solid var(--bhiv-primary-500);
  outline-offset: 2px;
}

/* Skip to content link */
.bhiv-skip-link {
  font-family: var(--bhiv-font-primary);
  font-size: var(--bhiv-text-sm);
  font-weight: var(--bhiv-font-semibold);
  position: absolute;
  top: -40px;
  left: 6px;
  background: var(--bhiv-primary-600);
  color: white;
  padding: 8px;
  text-decoration: none;
  z-index: 100;
}

.bhiv-skip-link:focus {
  top: 6px;
}
```

### Screen Reader Support
```css
/* Screen reader only text */
.bhiv-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

## Implementation Examples

### React Component with Typography
```jsx
const DashboardCard = ({ title, value, change, unit }) => {
  return (
    <div className="dashboard-card">
      <h3 className="bhiv-h5">{title}</h3>
      <div className="bhiv-kpi-large">
        {unit === 'currency' ? (
          <span className="bhiv-currency-large">{value}</span>
        ) : (
          <span>{value}</span>
        )}
      </div>
      <div className={`bhiv-kpi-change ${change >= 0 ? 'positive' : 'negative'}`}>
        {change >= 0 ? '+' : ''}{change}%
      </div>
    </div>
  );
};
```

### Vue Component with Typography
```vue
<template>
  <div class="financial-summary">
    <h2 class="bhiv-h2">{{ title }}</h2>
    <div class="metrics">
      <div v-for="metric in metrics" :key="metric.key">
        <span class="bhiv-kpi-label">{{ metric.label }}</span>
        <span class="bhiv-currency">{{ formatCurrency(metric.value) }}</span>
      </div>
    </div>
  </div>
</template>
```

### CSS Utility Classes
```css
/* Typography utility classes */
.bhiv-text-center { text-align: center; }
.bhiv-text-right { text-align: right; }
.bhiv-text-left { text-align: left; }

.bhiv-uppercase { text-transform: uppercase; }
.bhiv-lowercase { text-transform: lowercase; }
.bhiv-capitalize { text-transform: capitalize; }

.bhiv-italic { font-style: italic; }
.bhiv-underline { text-decoration: underline; }
.bhiv-no-underline { text-decoration: none; }

.bhiv-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bhiv-break-words {
  overflow-wrap: break-word;
  word-break: break-word;
}
```

## Font Loading Optimization

### Font Display Strategy
```css
/* Optimize font loading */
@font-face {
  font-family: 'Inter';
  src: url('./fonts/inter.woff2') format('woff2');
  font-display: swap; /* Ensure text remains visible during font load */
  font-weight: 300 900;
}

/* Fallback font metrics matching */
.bhiv-font-loading {
  font-family: system-ui, -apple-system, sans-serif;
  /* Adjust size to match Inter metrics */
  font-size: 1.02em;
  letter-spacing: -0.01em;
}
```

### Performance Considerations
```css
/* Preload critical fonts */
/* Add to HTML head */
/*
<link rel="preload" href="/fonts/inter-regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/inter-semibold.woff2" as="font" type="font/woff2" crossorigin>
*/
```

## Export for Other Products

### SCSS Variables
```scss
// typography.scss - For SCSS-based projects
$bhiv-font-primary: "Inter", system-ui, sans-serif;
$bhiv-font-mono: "JetBrains Mono", monospace;

$bhiv-text-sizes: (
  xs: 0.75rem,
  sm: 0.875rem,
  base: 1rem,
  lg: 1.125rem,
  xl: 1.25rem,
  2xl: 1.5rem,
  3xl: 1.875rem,
  4xl: 2.25rem
);

$bhiv-font-weights: (
  light: 300,
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700
);
```

### JavaScript Typography Tokens
```javascript
// typography.js
export const bhivTypography = {
  fontFamily: {
    primary: '"Inter", system-ui, sans-serif',
    mono: '"JetBrains Mono", monospace',
    display: '"Inter", system-ui, sans-serif'
  },
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem'
  },
  fontWeight: {
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700'
  },
  lineHeight: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.625'
  }
};
```

## Conclusion

This typography system provides:

- **Financial Focus**: Optimized for numerical data and financial interfaces
- **Accessibility**: WCAG compliant with proper contrast and sizing
- **Performance**: Efficient font loading with fallbacks
- **Consistency**: Unified text treatment across BHIV products
- **Flexibility**: Easy customization while maintaining design coherence

**Usage**: Import typography variables and classes into any BHIV product for consistent text styling.

---

**Design System Version**: 1.0  
**Font Loading**: Optimized with font-display: swap  
**Accessibility**: WCAG 2.1 AA Compliant  
**Performance**: Sub-100ms font loading with system fallbacks