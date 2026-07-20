import clsx from 'clsx';
import { AlertTriangle } from 'lucide-react';
import { Card, Badge } from '../common';

const severityOrder = ['HIGH', 'MEDIUM', 'LOW'];

const severityBadge = {
  HIGH: 'danger',
  MEDIUM: 'warning',
  LOW: 'success',
};

const SignalStackPanel = ({ groupedSignals, selectedSignalId, onSelectSignal }) => {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-semibold text-foreground">Signal Stack</h2>
        <Badge variant="info">{Object.values(groupedSignals).flat().length} active</Badge>
      </div>

      <p className="text-xs text-muted-foreground mb-4">
        Prioritized by severity and variance impact.
      </p>

      <div className="space-y-4">
        {severityOrder.map((severity) => {
          const items = groupedSignals[severity] || [];
          if (!items.length) return null;

          return (
            <section key={severity}>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-semibold text-muted-foreground tracking-wide">{severity} RISK</h3>
                <Badge variant={severityBadge[severity]} size="sm">
                  {items.length}
                </Badge>
              </div>

              <div className="space-y-2">
                {items.map((signal) => (
                  <button
                    key={signal.id}
                    onClick={() => onSelectSignal(signal)}
                    className={clsx(
                      'w-full text-left p-3 rounded-xl border transition-all duration-200',
                      selectedSignalId === signal.id
                        ? 'border-primary bg-primary/10'
                        : 'border-border/60 bg-muted/30 hover:bg-muted/60'
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-xs text-muted-foreground">{signal.signal_type}</p>
                        <p className="text-sm font-medium text-foreground leading-5">{signal.label}</p>
                      </div>
                      <AlertTriangle className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <Badge variant={severityBadge[signal.severity]} size="sm">
                        {signal.severity}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        Variance {signal.variance_pct > 0 ? '+' : ''}
                        {signal.variance_pct.toFixed(1)}%
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </Card>
  );
};

export default SignalStackPanel;
