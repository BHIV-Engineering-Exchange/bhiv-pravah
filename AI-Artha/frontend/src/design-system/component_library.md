# BHIV Design System — Component Library

## Overview
Reusable card components extracted from ARTHA dashboard. Each component below can be adopted
by any BHIV product without copying ARTHA source code. Props, usage examples, and extension
notes are provided.

---

## 1. KPI Card

**Purpose:** Display a single key performance indicator — a headline number with trend indicator, label, and optional icon.  
**ARTHA Source:** `Dashboard.jsx` — the KPI row (4-card grid)

### Props
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `title` | `string` | ✓ | — | Label above the metric (e.g. "Total Revenue") |
| `value` | `number \| string` | ✓ | — | Primary metric value |
| `change` | `number` | — | `0` | % change vs prior period |
| `changeType` | `'increase' \| 'decrease'` | — | `'increase'` | Direction of change (controls arrow icon color) |
| `icon` | `ReactNode` | — | — | Icon displayed top-right of card |
| `iconColor` | `string` | — | `'blue'` | Tailwind color name for icon bg (blue, red, yellow, green) |
| `isCurrency` | `boolean` | — | `true` | If false, renders raw number not currency-formatted |
| `format` | `'currency' \| 'count' \| 'percent'` | — | `'currency'` | Value formatting mode |
| `className` | `string` | — | — | Additional CSS classes |

### Example Usage
```jsx
import { DollarSign, TrendingUp } from 'lucide-react';
import { KPICard } from '@bhiv/design-system';

<KPICard
  title="Total Revenue"
  value={2450000}
  change={12.4}
  changeType="increase"
  icon={<DollarSign className="w-5 h-5 text-blue-600" />}
  iconColor="blue"
  format="currency"
/>

<KPICard
  title="Pending Invoices"
  value={14}
  change={-3}
  changeType="decrease"
  isCurrency={false}
  format="count"
/>
```

### Reference Implementation
```jsx
const KPICard = ({ title, value, change, changeType, icon, iconColor = 'blue', isCurrency = true, className }) => (
  <Card className={clsx('p-6', className)}>
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <p className="text-2xl font-bold text-foreground mt-1">
          {isCurrency ? formatCurrency(value) : value}
        </p>
      </div>
      {icon && (
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-${iconColor}-100`}>
          {icon}
        </div>
      )}
    </div>
    {change !== 0 && (
      <div className="flex items-center mt-4">
        {changeType === 'increase'
          ? <ArrowUpRight className="w-4 h-4 text-green-500" />
          : <ArrowDownRight className="w-4 h-4 text-red-500" />
        }
        <span className={`text-sm font-medium ${changeType === 'increase' ? 'text-green-600' : 'text-red-600'}`}>
          {Math.abs(change)}%
        </span>
        <span className="text-sm text-muted-foreground ml-1">vs last month</span>
      </div>
    )}
  </Card>
);
```

### Screenshot
> Rendered as a white card with title label (muted, sm), bold 2xl number, colored icon top-right, and green/red trend arrow bottom-left.

### Extension Notes
- Add `sparkline` prop to render a mini trend line inside the card
- Add `target` prop to show a progress bar toward a goal
- For real-time data, add `lastUpdated` timestamp below the value

---

## 2. Alert Card

**Purpose:** Surface a system alert, error, or compliance issue with severity indication.  
**ARTHA Source:** `FinancialIntelligenceDashboard.jsx` — error surface, runtime banner

### Props
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `title` | `string` | ✓ | — | Alert heading |
| `message` | `string` | ✓ | — | Alert body text |
| `severity` | `'critical' \| 'high' \| 'medium' \| 'low' \| 'info'` | — | `'info'` | Controls color scheme |
| `icon` | `ReactNode` | — | auto from severity | Override default severity icon |
| `action` | `{ label: string, onClick: () => void }` | — | — | Optional action button |
| `dismissible` | `boolean` | — | `false` | Show dismiss (×) button |
| `className` | `string` | — | — | Additional CSS |

### Severity Color Map
| Severity | Border | Background | Icon |
|----------|--------|-----------|------|
| `critical` | `border-destructive/40` | `bg-destructive/8` | `AlertCircle` red |
| `high` | `border-destructive/30` | `bg-destructive/5` | `AlertCircle` red |
| `medium` | `border-warning/30` | `bg-warning/5` | `AlertTriangle` amber |
| `low` | `border-info/30` | `bg-info/5` | `Info` blue |
| `info` | `border-border/30` | `bg-muted/50` | `Info` gray |

### Example Usage
```jsx
<AlertCard
  title="Signal Fetch Failed"
  message="Cannot reach /api/v1/signals — HTTP 503"
  severity="high"
  action={{ label: 'Retry', onClick: handleRetry }}
/>

<AlertCard
  title="Backend Unavailable"
  message="Cannot reach the Artha API on port 5000."
  severity="critical"
  action={{ label: 'Retry Connection', onClick: recheck }}
/>
```

### Reference Implementation
```jsx
const AlertCard = ({ title, message, severity = 'info', action, className }) => {
  const styles = {
    critical: 'border-destructive/40 bg-destructive/8',
    high:     'border-destructive/30 bg-destructive/5',
    medium:   'border-warning/30 bg-warning/5',
    info:     'border-border/30 bg-muted/50',
  };
  return (
    <Card className={clsx('p-3', styles[severity] || styles.info, className)}>
      <div className="flex items-center gap-2">
        <AlertCircle className="w-4 h-4 text-destructive flex-shrink-0" />
        <div>
          <p className="text-xs font-semibold text-destructive uppercase tracking-wide">{title}</p>
          <p className="text-xs text-muted-foreground">{message}</p>
        </div>
      </div>
      {action && (
        <button onClick={action.onClick} className="mt-2 text-xs text-primary hover:underline">
          {action.label}
        </button>
      )}
    </Card>
  );
};
```

### Extension Notes
- Add `timestamp` prop to show when the alert was raised
- Add `traceId` prop to link to trace reconstruction
- For stacked alerts, wrap in `<div className="space-y-2">` — never merge into one card

---

## 3. Timeline Card

**Purpose:** Display a time-series area chart (bank transactions, revenue trends).  
**ARTHA Source:** `Dashboard.jsx` — Bank Transaction Timeline section

### Props
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `title` | `string` | ✓ | — | Card title |
| `description` | `string` | — | — | Subtitle below title |
| `data` | `Array<{label, date, credits, debits}>` | ✓ | — | Chart data points |
| `height` | `number` | — | `300` | Chart area height in px |
| `lines` | `Array<{key, color, name}>` | — | — | Line/area series config |
| `currency` | `boolean` | — | `true` | Format Y-axis and tooltip as currency |
| `className` | `string` | — | — | Additional CSS |

### Example Usage
```jsx
<TimelineCard
  title="Bank Transaction Timeline"
  description="Daily credits and debits from uploaded bank statements"
  data={bankTimelineChart}
  lines={[
    { key: 'credits', color: '#10b981', name: 'Credits' },
    { key: 'debits',  color: '#ef4444', name: 'Debits' },
  ]}
/>
```

### Reference Implementation (Recharts)
```jsx
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const TimelineCard = ({ title, description, data, height = 300, lines }) => (
  <Card>
    <Card.Title>{title}</Card.Title>
    {description && <p className="text-sm text-muted-foreground mb-4">{description}</p>}
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="label" />
        <YAxis tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
        <Tooltip formatter={(v, name) => [formatCurrency(v), name]} />
        <Legend />
        {lines.map(line => (
          <Area key={line.key} type="monotone" dataKey={line.key}
            stroke={line.color} fill={line.color} fillOpacity={0.2} name={line.name} />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  </Card>
);
```

### Extension Notes
- Add `dateRange` selector to let users zoom in/out
- Add `annotations` prop for vertical event markers (e.g. "Bank statement imported")
- Support `BarChart` variant via `chartType` prop for non-cumulative data

---

## 4. Telemetry Card

**Purpose:** Show a computed health/performance metric with progress ring and severity badge.  
**ARTHA Source:** `FinancialIntelligenceDashboard.jsx` — Health Score, Budget Risk Level, Active Issues

### Props
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `title` | `string` | ✓ | — | Metric label |
| `value` | `number \| string` | ✓ | — | Primary value |
| `icon` | `ReactNode` | ✓ | — | Icon component |
| `iconBg` | `string` | — | `'bg-primary/10'` | Background class for icon container |
| `variant` | `'number' \| 'badge'` | — | `'number'` | Render value as raw number or badge |
| `badgeVariant` | `'success' \| 'warning' \| 'danger'` | — | — | Badge color (if variant=badge) |

### Example Usage
```jsx
<TelemetryCard
  title="Financial Health Score"
  value={87}
  icon={<HeartPulse className="w-5 h-5 text-primary" />}
  iconBg="bg-primary/10"
  variant="number"
/>

<TelemetryCard
  title="Budget Risk Level"
  value="HIGH"
  icon={<ShieldAlert className="w-5 h-5 text-warning" />}
  iconBg="bg-warning/10"
  variant="badge"
  badgeVariant="danger"
/>
```

### Reference Implementation
```jsx
const TelemetryCard = ({ title, value, icon, iconBg = 'bg-primary/10', variant = 'number', badgeVariant }) => (
  <Card className="p-4">
    <div className="flex items-center gap-3">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${iconBg}`}>
        {icon}
      </div>
      <div>
        <p className="text-xs text-muted-foreground">{title}</p>
        {variant === 'number'
          ? <p className="text-2xl font-bold text-foreground">{value}</p>
          : <Badge variant={badgeVariant}>{value}</Badge>
        }
      </div>
    </div>
  </Card>
);
```

### Extension Notes
- Add `trend` prop (arrow icon) to show change direction
- Add `sparkline` prop for a mini 7-day chart inside the card
- Add `threshold` prop to color the value red/green based on a target

---

## 5. Executive Card

**Purpose:** High-level summary with a headline, sub-metric, and optional action link.  
Suitable for financial summaries presented to non-technical executives.  
**ARTHA Source:** Dashboard header section, compliance summary cards

### Props
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `headline` | `string` | ✓ | — | Bold headline metric |
| `label` | `string` | ✓ | — | Descriptive label |
| `subMetric` | `string` | — | — | Secondary number or text |
| `subLabel` | `string` | — | — | Label for sub-metric |
| `status` | `'positive' \| 'negative' \| 'neutral'` | — | `'neutral'` | Color signal |
| `action` | `{ label: string, onClick: fn }` | — | — | Optional drill-down link |
| `accentColor` | `string` | — | `'blue'` | Top border accent color name |

### Example Usage
```jsx
<ExecutiveCard
  headline="₹24,50,000"
  label="Total Revenue (YTD)"
  subMetric="+12.4%"
  subLabel="vs last year"
  status="positive"
  action={{ label: 'View P&L', onClick: () => navigate('/reports/profit-loss') }}
  accentColor="green"
/>
```

### Extension Notes
- Add `comparisonPeriod` to clarify what the sub-metric is compared against
- Add `lastUpdated` timestamp for real-time data freshness indication
- Use in a 3-column grid for an executive-facing overview page

---

## 6. Observability Card

**Purpose:** Display a single trace step or pipeline check result with expand/collapse detail.  
**ARTHA Source:** Signal trace reconstruction (`/signals/trace/:traceId`), SignalDetailEngine

### Props
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `step` | `number` | ✓ | — | Step number in trace chain (1–5) |
| `label` | `string` | ✓ | — | Step name (e.g. "Journal Entries") |
| `found` | `boolean` | ✓ | — | Was this step found in DB? |
| `data` | `object \| array` | — | — | Raw data to display in expandable panel |
| `isLast` | `boolean` | — | `false` | Controls connector line rendering |

### Example Usage
```jsx
{traceSteps.map((step, i) => (
  <ObservabilityCard
    key={step.step}
    step={step.step}
    label={step.label}
    found={step.found}
    data={step.data}
    isLast={i === traceSteps.length - 1}
  />
))}
```

### Reference Implementation
```jsx
const ObservabilityCard = ({ step, label, found, data, isLast }) => (
  <div className="flex gap-3">
    <div className="flex flex-col items-center">
      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
        ${found ? 'bg-success/20 text-success' : 'bg-destructive/20 text-destructive'}`}>
        {found ? '✓' : '✗'}
      </div>
      {!isLast && <div className="w-px flex-1 bg-border/40 mt-1" />}
    </div>
    <div className="pb-4 flex-1">
      <p className="text-sm font-medium text-foreground">{`Step ${step}: ${label}`}</p>
      {data && (
        <pre className="text-xs font-mono text-muted-foreground mt-1 bg-muted/50 rounded p-2 overflow-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  </div>
);
```

### Extension Notes
- Add `duration` prop to show how long this trace step took
- Add `error` prop to display failure reason when `found=false`
- Chain multiple ObservabilityCards in a `<div className="space-y-0">` to create the connected timeline

---

## 7. Runtime Status Card

**Purpose:** Display backend connectivity status with mode indicator.  
**ARTHA Source:** `RuntimeModeBanner.jsx` — Phase 1B implementation

### Props
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `mode` | `'CHECKING' \| 'BACKEND_CONNECTED' \| 'BACKEND_DEGRADED' \| 'BACKEND_UNAVAILABLE' \| 'MOCK_MODE'` | ✓ | — | Current runtime mode |
| `lastChecked` | `Date \| string` | — | — | Timestamp of last check |
| `onRecheck` | `() => void` | — | — | Callback for retry button |
| `compact` | `boolean` | — | `false` | Compact banner vs full card |

### Mode → Visual Map
| Mode | Color | Icon | Message |
|------|-------|------|---------|
| `CHECKING` | Muted | Spinner | "Connecting to backend…" |
| `BACKEND_CONNECTED` | Green | CheckCircle | "Connected — live data" |
| `BACKEND_DEGRADED` | Amber | AlertTriangle | "Partial — some APIs unavailable" |
| `BACKEND_UNAVAILABLE` | Red | WifiOff | "Offline — backend unreachable" |
| `MOCK_MODE` | Purple | Database | "Mock mode — development only" |

### Example Usage
```jsx
<RuntimeStatusCard
  mode={mode}
  lastChecked={lastChecked}
  onRecheck={recheck}
  compact
/>
```

### Extension Notes
- Subscribe to a WebSocket event for live mode updates without page refresh
- Add `services` prop to show per-service health (DB, Redis, SETU)
- In production: display mode CONNECTED or DEGRADED only — never show MOCK_MODE

---

## 8. Compliance Card

**Purpose:** Display a compliance filing period summary with filing-ready status.  
**ARTHA Source:** `GSTDashboard.jsx`, `TDSManagement.jsx`

### Props
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `filingType` | `'GSTR-1' \| 'GSTR-3B' \| 'Form26Q' \| string` | ✓ | — | Filing type label |
| `period` | `string` | ✓ | — | Reporting period (e.g. "April 2026") |
| `status` | `'ready' \| 'not_ready' \| 'filed' \| 'pending'` | ✓ | — | Filing status |
| `summary` | `object` | — | — | Key metrics: `{ outputTax, itcClaim, netLiability }` |
| `errorCount` | `number` | — | `0` | Validation errors blocking filing |
| `onGenerate` | `() => void` | — | — | Callback for Generate button |
| `onViewErrors` | `() => void` | — | — | Callback for View Errors button |

### Status → Visual Map
| Status | Badge Color | Actions |
|--------|------------|---------|
| `ready` | Green "READY" | [Download] [File Now] |
| `not_ready` | Red "NOT READY" | [View Errors] [Fix Issues] |
| `filed` | Blue "FILED" | [View Receipt] |
| `pending` | Amber "PENDING" | [Generate] |

### Example Usage
```jsx
<ComplianceCard
  filingType="GSTR-1"
  period="May 2026"
  status="not_ready"
  summary={{ outputTax: 84000, itcClaim: 12000, netLiability: 72000 }}
  errorCount={3}
  onGenerate={handleGenerate}
  onViewErrors={handleViewErrors}
/>
```

### Extension Notes
- Add `dueDate` prop with auto-alert if within 3 days
- Add `signalCount` prop to link to related ComplianceSignals
- Support `historical` prop to show past filings in a timeline below the card

---

## Base Card Component (Foundation)

All the above components are built on this base:

```jsx
// frontend/src/components/common/Card.jsx
const Card = ({ children, className, padding = true, variant = 'default', ...props }) => {
  const variants = {
    default:  'bg-card border-border/30',
    glass:    'bg-card/80 backdrop-blur-xl border-border/50',
    elevated: 'bg-card border-border/30 shadow-lg',
  };
  return (
    <div
      className={clsx('rounded-2xl border transition-all duration-300',
        variants[variant] || variants.default,
        padding && 'p-6',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
Card.Header = CardHeader;
Card.Title = CardTitle;
Card.Description = CardDescription;
Card.Content = CardContent;
Card.Footer = CardFooter;
```

**Key properties:**
- `rounded-2xl` — 24 px border radius on all cards
- `border border-border/30` — subtle 30% opacity border
- `transition-all duration-300` — smooth hover animations
- Variants: `default`, `glass` (glassmorphism), `elevated` (shadow)

---

## Other Common Components

| Component | File | Purpose |
|-----------|------|---------|
| `Badge` | `Badge.jsx` | Status label: success/warning/danger/info/muted variants |
| `Button` | `Button.jsx` | primary/secondary/ghost/outline/destructive variants |
| `Loading` | `Loading.jsx` | `<Loading.Page />` full-page spinner; `<Loading size="md" />` inline |
| `EmptyState` | `EmptyState.jsx` | Zero-state with icon, message, optional CTA |
| `Table` | `Table.jsx` | Sortable data table with pagination |
| `Input` | `Input.jsx` | Form input with validation states |
| `Modal` | `Modal.jsx` | Overlay dialog with backdrop |
| `PageHeader` | `PageHeader.jsx` | Consistent page title + CTA row |

---

**Design System Version**: 1.0  
**Last Updated**: June 2026  
**Dependencies**: lucide-react (icons), recharts (charts), clsx (class merging)  
