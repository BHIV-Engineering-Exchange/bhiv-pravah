'use client';

import React from 'react';
import { useLiveDashboard } from '../../hooks/useBackend';
import { 
  BarChart3, 
  Activity, 
  TrendingUp, 
  AlertOctagon, 
  DollarSign,
  Loader2
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  LineChart, 
  Line 
} from 'recharts';

export default function Analytics() {
  const { data: dashboard, isLoading } = useLiveDashboard();

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-20 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <span className="text-xs text-muted-foreground font-mono">CALCULATING ECOSYSTEM ANALYTICS...</span>
      </div>
    );
  }

  const runtimes = dashboard?.monitored_services || dashboard?.live_production_monitoring || [];

  // Generate charts data
  const chartsData = runtimes.map(item => ({
    name: item.name,
    latency: item.response_time_ms,
    cpu: item.cpu_percent,
    memory: item.memory_percent,
    errors: item.errors_24h,
    success: item.uptime_percent,
  }));

  return (
    <div className="flex-1 flex flex-col gap-6 font-mono text-xs">
      
      {/* Header */}
      <header className="flex justify-between items-end pb-4 border-b border-border/60">
        <div>
          <h2 className="text-xl font-bold font-sans tracking-tight text-foreground flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary" />
            Analytics Center
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Aggregated system latency histograms, CPU workloads, error frequencies, and certification throughput
          </p>
        </div>
      </header>

      {/* Grid of stats */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="premium-card flex flex-col gap-1 relative overflow-hidden">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Average Latency (EMA p50)</span>
          <span className="text-xl font-bold text-foreground font-sans">
            {dashboard?.ml_intelligence?.latency_ema_p50 !== undefined && dashboard?.ml_intelligence?.latency_ema_p50 !== null
              ? `${Number(dashboard.ml_intelligence.latency_ema_p50).toFixed(1)}ms`
              : (runtimes.length > 0 ? `${Math.round(runtimes.reduce((acc, curr) => acc + curr.response_time_ms, 0) / runtimes.length)}ms` : 'N/A')}
          </span>
          <div className="absolute right-3 top-3 opacity-10">
            <Activity className="w-8 h-8 text-primary" />
          </div>
        </div>

        <div className="premium-card flex flex-col gap-1 relative overflow-hidden">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Accumulated Run Cost</span>
          <span className="text-xl font-bold text-foreground/60 font-sans">
            N/A
          </span>
          <div className="absolute right-3 top-3 opacity-10">
            <DollarSign className="w-8 h-8 text-emerald-500" />
          </div>
        </div>

        <div className="premium-card flex flex-col gap-1 relative overflow-hidden">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Certification Success Rate</span>
          <span className="text-xl font-bold text-foreground font-sans">
            {dashboard?.ml_intelligence?.cert_success_rate_rolling !== undefined && dashboard?.ml_intelligence?.cert_success_rate_rolling !== null
              ? `${(Number(dashboard.ml_intelligence.cert_success_rate_rolling) * 100).toFixed(1)}%`
              : 'N/A'}
          </span>
          <div className="absolute right-3 top-3 opacity-10">
            <TrendingUp className="w-8 h-8 text-primary" />
          </div>
        </div>

        <div className="premium-card flex flex-col gap-1 relative overflow-hidden">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Throughput (1m Rolling)</span>
          <span className="text-xl font-bold text-foreground font-sans">
            {dashboard?.ml_intelligence?.throughput_rps_1m !== undefined && dashboard?.ml_intelligence?.throughput_rps_1m !== null
              ? `${Number(dashboard.ml_intelligence.throughput_rps_1m).toFixed(2)} rps`
              : 'N/A'}
          </span>
          <div className="absolute right-3 top-3 opacity-10">
            <Activity className="w-8 h-8 text-amber-500" />
          </div>
        </div>
      </section>

      {/* Latency histogram */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Latency by service */}
        <div className="premium-card flex flex-col gap-4">
          <span className="font-bold text-xs uppercase tracking-wider text-muted-foreground border-b border-border/40 pb-2">Response Latency Histogram</span>
          <div className="h-64 text-[10px]">
            {chartsData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorBarLatency" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="var(--primary)" stopOpacity={0.2}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="name" stroke="var(--muted-foreground)" />
                  <YAxis stroke="var(--muted-foreground)" />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }} />
                  <Bar dataKey="latency" name="Latency (ms)" fill="url(#colorBarLatency)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground italic text-center">
                No active monitored services available for latency histogram.
              </div>
            )}
          </div>
        </div>

        {/* Success / Error comparison */}
        <div className="premium-card flex flex-col gap-4">
          <span className="font-bold text-xs uppercase tracking-wider text-muted-foreground border-b border-border/40 pb-2">Downstream Stability Uptime</span>
          <div className="h-64 text-[10px]">
            {chartsData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="name" stroke="var(--muted-foreground)" />
                  <YAxis domain={[80, 100]} stroke="var(--muted-foreground)" />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }} />
                  <Line type="monotone" dataKey="success" name="Success Rate %" stroke="#10b981" strokeWidth={2.5} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground italic text-center">
                No active monitored services available for stability uptime.
              </div>
            )}
          </div>
        </div>

      </section>

      {/* Failure frequencies */}
      <section className="premium-card flex flex-col gap-4 mt-2">
        <span className="font-bold text-xs uppercase tracking-wider text-muted-foreground border-b border-border/40 pb-2">Failure Frequency (Anomalies last 24h)</span>
        <div className="h-64 text-[10px]">
          {chartsData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorErrors" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="name" stroke="var(--muted-foreground)" />
                <YAxis stroke="var(--muted-foreground)" />
                <Tooltip contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }} />
                <Area type="monotone" dataKey="errors" name="Anomalies detected" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorErrors)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-muted-foreground italic text-center">
              No active monitored services available for anomaly tracking.
            </div>
          )}
        </div>
      </section>

    </div>
  );
}
