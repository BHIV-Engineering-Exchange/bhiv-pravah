'use client';

import React, { useState } from 'react';
import { 
  useLiveDashboard, 
  useIngestLink, 
  useRemoveLink,
  useObserverEvents
} from '../hooks/useBackend';
import { 
  Activity, 
  Cpu, 
  HardDrive, 
  TrendingUp, 
  AlertTriangle, 
  Plus, 
  Trash2, 
  CheckCircle2, 
  ShieldAlert, 
  ExternalLink,
  ArrowRightLeft,
  Loader2
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { toast } from 'sonner';

export default function Dashboard() {
  const { data: dashboard, isLoading, isError, refetch } = useLiveDashboard();
  const { data: eventsData } = useObserverEvents(10);
  const ingestMutation = useIngestLink();
  const removeMutation = useRemoveLink();

  const [newLink, setNewLink] = useState('');

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-20 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <span className="text-xs text-muted-foreground font-mono">LOADING REAL-TIME METRICS...</span>
      </div>
    );
  }

  if (isError || !dashboard) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-20 gap-4 text-center">
        <ShieldAlert className="w-12 h-12 text-rose-500" />
        <div>
          <h3 className="font-bold text-sm font-sans">CONTROL PLANE UNREACHABLE</h3>
          <p className="text-xs text-muted-foreground mt-1 max-w-sm">
            Failed to connect to the Decision Brain API on port 8000. Ensure the backend stack is running locally.
          </p>
        </div>
        <button 
          onClick={() => refetch()}
          className="px-4 py-2 bg-primary text-primary-foreground font-sans text-xs font-semibold rounded-lg hover:opacity-90 transition-opacity"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLink.trim()) return;
    
    toast.promise(ingestMutation.mutateAsync(newLink), {
      loading: 'Ingesting repository link...',
      success: (res) => {
        if (res.success) {
          setNewLink('');
          return `Successfully ingested: ${res.ingested_link?.name || newLink}`;
        }
        throw new Error(res.error || 'Failed to ingest link');
      },
      error: (err) => err.message
    });
  };

  const handleRemove = async (link: string) => {
    toast.promise(removeMutation.mutateAsync(link), {
      loading: 'Removing monitored link...',
      success: (res) => {
        if (res.success) {
          return 'Successfully removed from monitoring';
        }
        throw new Error(res.error || 'Failed to remove link');
      },
      error: (err) => err.message
    });
  };

  // Prepare chart data
  const latencyData = dashboard.live_production_monitoring.map(item => ({
    name: item.name,
    latency: item.response_time_ms,
    uptime: item.uptime_percent,
  }));

  const resourceData = dashboard.live_production_monitoring.map(item => ({
    name: item.name,
    cpu: item.cpu_percent,
    memory: item.memory_percent,
  }));

  // Health distribution
  const healthyCount = dashboard.live_production_monitoring.filter(s => s.status === 'CONNECTED').length;
  const criticalCount = dashboard.live_production_monitoring.filter(s => s.status === 'CRITICAL' || s.status === 'DISCONNECTED').length;
  const degradedCount = dashboard.live_production_monitoring.filter(s => s.status === 'DEGRADED').length;

  const pieData = [
    { name: 'Healthy', value: healthyCount, color: '#10b981' },
    { name: 'Degraded', value: degradedCount, color: '#f59e0b' },
    { name: 'Critical', value: criticalCount, color: '#ef4444' },
  ].filter(d => d.value > 0);

  return (
    <div className="flex-1 flex flex-col gap-6 font-sans">
      
      {/* Dashboard Top Header */}
      <header className="flex justify-between items-end pb-4 border-b border-border/60">
        <div>
          <h2 className="text-xl font-bold font-sans tracking-tight text-foreground">
            {dashboard.header.title}
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            {dashboard.header.subtitle} &bull; Generated at {new Date(dashboard.generated_at).toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center gap-1.5 status-pill healthy font-mono text-[10px]">
          <span className="pulse-dot healthy" />
          SYSTEM OPERATIONAL
        </div>
      </header>

      {/* Top 4 Stats Rows */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {dashboard.system_health.map((s, idx) => {
          const isHealth = s.label.toLowerCase().includes('health');
          return (
            <div key={idx} className="premium-card flex flex-col gap-1 relative overflow-hidden">
              <div className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider">{s.label}</div>
              <div className="text-xl font-bold tracking-tight text-foreground">{s.value}</div>
              <div className="absolute right-3 top-3 opacity-15">
                {isHealth ? <Activity className="w-8 h-8 text-emerald-500" /> : <Cpu className="w-8 h-8 text-primary" />}
              </div>
            </div>
          );
        })}
      </section>

      {/* Charts Grid */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Latency History */}
        <div className="lg:col-span-2 premium-card flex flex-col gap-4">
          <h4 className="font-bold text-xs uppercase tracking-wider text-muted-foreground font-mono">Response Times (ms)</h4>
          <div className="h-64 w-full text-[10px] font-mono">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={latencyData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                <XAxis dataKey="name" stroke="var(--muted-foreground)" />
                <YAxis stroke="var(--muted-foreground)" />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)', color: 'var(--foreground)' }}
                />
                <Area type="monotone" dataKey="latency" name="Latency (ms)" stroke="var(--primary)" fillOpacity={1} fill="url(#colorLatency)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status Distribution */}
        <div className="premium-card flex flex-col gap-4">
          <h4 className="font-bold text-xs uppercase tracking-wider text-muted-foreground font-mono">Service Distribution</h4>
          <div className="flex-1 flex flex-col items-center justify-center min-h-[220px]">
            {pieData.length > 0 ? (
              <div className="h-44 w-full text-[10px] font-mono relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={65}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                {/* Center metric */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <span className="text-xl font-bold">{dashboard.live_production_monitoring.length}</span>
                  <span className="text-[9px] text-muted-foreground font-sans">MONITORED</span>
                </div>
              </div>
            ) : (
              <span className="text-muted-foreground text-xs font-mono">No nodes active.</span>
            )}
            <div className="flex gap-4 justify-center text-[10px] font-mono mt-2">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-emerald-500" /> Healthy ({healthyCount})</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-amber-500" /> Degraded ({degradedCount})</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-rose-500" /> Critical ({criticalCount})</span>
            </div>
          </div>
        </div>
      </section>

      {/* Resource Util & failover row */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Resource Usage bar chart */}
        <div className="lg:col-span-2 premium-card flex flex-col gap-4">
          <h4 className="font-bold text-xs uppercase tracking-wider text-muted-foreground font-mono">Resource Utilization</h4>
          <div className="h-56 w-full text-[10px] font-mono">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={resourceData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                <XAxis dataKey="name" stroke="var(--muted-foreground)" />
                <YAxis stroke="var(--muted-foreground)" />
                <Tooltip contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }} />
                <Bar dataKey="cpu" name="CPU %" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="memory" name="Memory %" fill="var(--secondary-foreground)" opacity={0.3} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Failover Domain Config */}
        <div className="premium-card flex flex-col gap-4 font-mono">
          <h4 className="font-bold text-xs uppercase tracking-wider text-muted-foreground">Failover Orchestrator</h4>
          <div className="flex flex-col gap-3.5 mt-2">
            <div className="flex items-center justify-between border-b border-border/40 pb-2">
              <span className="text-xs text-muted-foreground">Active Gate:</span>
              <span className="text-xs font-extrabold text-primary flex items-center gap-1">
                <ArrowRightLeft className="w-3.5 h-3.5" />
                {dashboard.auto_failover_status.active_domain}
              </span>
            </div>
            <div className="flex flex-col gap-2">
              <span className="text-[10px] text-muted-foreground uppercase">Domain Failover Queue:</span>
              {dashboard.auto_failover_status.domains.map((dom, i) => (
                <div key={i} className="flex justify-between items-center bg-secondary/30 border border-border/40 px-3 py-1.5 rounded text-[10px]">
                  <span>{dom.name}</span>
                  <span className={`font-semibold ${dom.status.includes('FAILOVER') ? 'text-primary' : 'text-emerald-500'}`}>{dom.status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

      </section>

      {/* Monitored Repos and Link Ingestions */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Monitored Links Ingestion table */}
        <div className="lg:col-span-2 premium-card flex flex-col gap-4 font-mono">
          <div className="flex justify-between items-center border-b border-border/60 pb-3">
            <h4 className="font-bold text-xs uppercase tracking-wider text-muted-foreground">Live Telemetry Ingestions</h4>
            
            {/* Form */}
            <form onSubmit={handleIngest} className="flex gap-2">
              <input 
                type="text"
                placeholder="https://github.com/org/repo"
                className="bg-background text-xs px-4 py-2.5 rounded-xl border border-border outline-none focus:border-primary placeholder-muted-foreground w-56 font-mono shadow-sm"
                value={newLink}
                onChange={(e) => setNewLink(e.target.value)}
              />
              <button 
                type="submit"
                disabled={ingestMutation.isPending}
                className="bg-primary hover:opacity-90 text-primary-foreground text-xs px-5 py-2.5 rounded-xl font-sans font-bold flex items-center gap-1.5 shrink-0 shadow-sm cursor-pointer border border-primary/20 active:scale-[0.98] transition-all"
              >
                <Plus className="w-3.5 h-3.5" /> Add
              </button>
            </form>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-[10px] divide-y divide-border">
              <thead>
                <tr className="text-muted-foreground">
                  <th className="pb-2 font-medium">Service name</th>
                  <th className="pb-2 font-medium">Domain</th>
                  <th className="pb-2 font-medium">Uptime</th>
                  <th className="pb-2 font-medium">Errors (24h)</th>
                  <th className="pb-2 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {dashboard.live_production_monitoring.map((item, idx) => (
                  <tr key={idx} className="group hover:bg-secondary/20">
                    <td className="py-2.5 font-semibold text-foreground flex items-center gap-1.5">
                      <span className={`w-1.5 h-1.5 rounded-full ${item.status === 'CONNECTED' ? 'bg-emerald-500' : (item.status === 'DEGRADED' ? 'bg-amber-500' : 'bg-rose-500')}`} />
                      {item.name}
                    </td>
                    <td className="py-2.5 text-muted-foreground max-w-[120px] truncate">{item.domain}</td>
                    <td className="py-2.5">{item.uptime_percent}%</td>
                    <td className="py-2.5 text-rose-500">{item.errors_24h}</td>
                    <td className="py-2.5 text-right">
                      {item.url.startsWith('http') && item.name !== 'BLACKHOLE' && item.name !== 'UNI_GURU' ? (
                        <button 
                          onClick={() => handleRemove(item.url)}
                          className="p-1 hover:text-rose-500 text-muted-foreground transition-colors"
                          title="Remove from monitoring"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      ) : (
                        <span className="text-[9px] text-muted-foreground italic">System Core</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live System Events feed */}
        <div className="premium-card flex flex-col gap-4 font-mono">
          <h4 className="font-bold text-xs uppercase tracking-wider text-muted-foreground">Ecosystem Timeline Events</h4>
          <div className="flex flex-col gap-3 py-1 overflow-y-auto max-h-[300px]">
            {dashboard.live_events.map((ev, i) => (
              <div key={i} className="flex gap-2.5 items-start text-[10px] leading-relaxed border-l-2 border-border pl-3.5 py-0.5">
                <div className="flex-1 flex flex-col gap-0.5">
                  <span className="text-foreground font-medium">{ev.title}</span>
                  <span className="text-[9px] text-muted-foreground">{ev.time_ago}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </section>

    </div>
  );
}
