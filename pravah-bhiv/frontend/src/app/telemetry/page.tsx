'use client';

import React, { useState } from 'react';
import { useObserverEvents, useUnifiedRegistryTrace } from '../../hooks/useBackend';
import { 
  Terminal, 
  Search, 
  Filter, 
  Database, 
  Activity, 
  ArrowRight,
  Info,
  Loader2
} from 'lucide-react';

export default function Telemetry() {
  const [limit, setLimit] = useState(100);
  const { data: eventsData, isLoading: eventsLoading, refetch } = useObserverEvents(limit);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedService, setSelectedService] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');

  // Unified trace ID search
  const [traceInput, setTraceInput] = useState('');
  const [searchTraceId, setSearchTraceId] = useState<string | null>(null);
  
  const { data: traceData, isLoading: traceLoading, error: traceError } = useUnifiedRegistryTrace(searchTraceId);

  const handleTraceSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (traceInput.trim()) {
      setSearchTraceId(traceInput.trim());
    } else {
      setSearchTraceId(null);
    }
  };

  if (eventsLoading) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-20 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <span className="text-xs text-muted-foreground font-mono">LOADING TELEMETRY STREAM...</span>
      </div>
    );
  }

  const events = eventsData?.events || [];

  // Filter events
  const filteredEvents = events.filter(ev => {
    const matchesSearch = searchQuery ? JSON.stringify(ev).toLowerCase().includes(searchQuery.toLowerCase()) : true;
    const matchesService = selectedService === 'all' ? true : ev.service.toLowerCase() === selectedService.toLowerCase();
    const matchesStatus = selectedStatus === 'all' ? true : ev.status.toLowerCase() === selectedStatus.toLowerCase();
    return matchesSearch && matchesService && matchesStatus;
  });

  // Extract unique services and statuses for filtering options
  const uniqueServices = Array.from(
    new Set(
      events
        .map((e: any) => (e.service || '').toLowerCase().trim())
        .filter(Boolean)
    )
  );
  const uniqueStatuses = Array.from(
    new Set(
      events
        .map((e: any) => (e.status || '').toLowerCase().trim())
        .filter(Boolean)
    )
  );

  const getStatusClass = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy': return 'status-pill healthy';
      case 'degraded': return 'status-pill degraded';
      case 'error':
      case 'unreachable':
      case 'crashed': return 'status-pill critical';
      default: return 'status-pill info';
    }
  };

  return (
    <div className="flex-1 flex flex-col gap-6 font-mono text-xs">
      
      {/* Header */}
      <header className="flex justify-between items-end pb-4 border-b border-border/60">
        <div>
          <h2 className="text-xl font-bold font-sans tracking-tight text-foreground flex items-center gap-2">
            <Terminal className="w-5 h-5 text-primary" />
            Telemetry Stream
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Audit real-time incoming events, logs, telemetry and registry lineage traces
          </p>
        </div>
      </header>

      {/* Trace ID Audit Registry search box */}
      <section className="premium-card flex flex-col gap-4">
        <span className="font-bold text-xs uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
          <Database className="w-4 h-4 text-primary" />
          Query Unified Evidence Registry
        </span>

        <form onSubmit={handleTraceSearch} className="flex gap-2">
          <input 
            type="text"
            placeholder="Input Trace ID (e.g. tr-12345)"
            className="flex-1 bg-secondary/40 text-foreground border border-border rounded-lg px-3 py-2 outline-none font-mono focus:border-primary text-xs"
            value={traceInput}
            onChange={(e) => setTraceInput(e.target.value)}
          />
          <button 
            type="submit"
            className="bg-primary hover:opacity-90 text-primary-foreground text-[10px] px-4 py-2 rounded-lg font-sans font-bold flex items-center gap-1.5 shrink-0"
          >
            Audit Trace <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Trace search results */}
        {traceLoading && (
          <div className="flex items-center gap-2 text-muted-foreground text-xs py-2">
            <Loader2 className="w-4 h-4 animate-spin text-primary" />
            <span>Verifying registry chain logs...</span>
          </div>
        )}

        {traceError && (
          <div className="text-rose-500 bg-rose-500/10 border border-rose-500/20 p-3 rounded-lg">
            Failed to fetch trace: {traceError.message || 'Trace ID not found in evidence pipeline'}
          </div>
        )}

        {traceData && (
          <div className="bg-secondary/40 border border-border p-4 rounded-lg flex flex-col gap-2">
            <span className="font-bold text-foreground">Trace Integrity Validated</span>
            <div className="grid grid-cols-2 gap-2 text-[10px] text-muted-foreground border-b border-border/40 pb-2">
              <div>Trace ID: <span className="text-foreground">{traceData.trace_id || searchTraceId}</span></div>
              <div>Nodes Validated: <span className="text-foreground">{traceData.lineage?.length || 1}</span></div>
            </div>
            <pre className="text-[10px] bg-black/40 border border-border p-3 rounded-lg overflow-x-auto text-muted-foreground max-h-[160px]">
              {JSON.stringify(traceData, null, 2)}
            </pre>
          </div>
        )}
      </section>

      {/* Main events table list with filters */}
      <section className="premium-card flex flex-col gap-4">
        
        {/* Filters Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/40 pb-3">
          <span className="font-bold text-xs uppercase tracking-wider text-muted-foreground">Active Telemetry Logs</span>
          
          <div className="flex flex-wrap items-center gap-3">
            {/* Search Input */}
            <div className="flex items-center gap-1.5 bg-secondary/40 border border-border px-2 py-1.5 rounded-lg w-40">
              <Search className="w-3.5 h-3.5 text-muted-foreground" />
              <input 
                type="text"
                placeholder="Search..."
                className="bg-transparent border-0 outline-none w-full text-[10px] text-foreground placeholder-muted-foreground"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Service filter */}
            <select 
              className="bg-secondary/40 text-muted-foreground border border-border rounded-lg px-2 py-1.5 outline-none font-mono text-[10px]"
              value={selectedService}
              onChange={(e) => setSelectedService(e.target.value)}
            >
              <option value="all">All Services</option>
              {uniqueServices.map((svc, i) => (
                <option key={i} value={svc}>{svc.toUpperCase()}</option>
              ))}
            </select>

            {/* Status filter */}
            <select 
              className="bg-secondary/40 text-muted-foreground border border-border rounded-lg px-2 py-1.5 outline-none font-mono text-[10px]"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
            >
              <option value="all">All Statuses</option>
              {uniqueStatuses.map((st, i) => (
                <option key={i} value={st}>{st.toLowerCase()}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[10px] divide-y divide-border">
            <thead>
              <tr className="text-muted-foreground">
                <th className="pb-2 font-medium">Time</th>
                <th className="pb-2 font-medium">Observed Source</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium">Latency</th>
                <th className="pb-2 font-medium">Message / Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {filteredEvents.length > 0 ? (
                filteredEvents.map((ev, idx) => (
                  <tr key={idx} className="hover:bg-secondary/20 transition-colors">
                    <td className="py-2.5 text-muted-foreground">{new Date(ev.ts + (ev.ts.endsWith('Z') ? '' : 'Z')).toLocaleTimeString()}</td>
                    <td className="py-2.5 font-semibold text-foreground uppercase">{ev.service}</td>
                    <td className="py-2.5">
                      <span className={getStatusClass(ev.status)}>{ev.status}</span>
                    </td>
                    <td className="py-2.5">{ev.latency_ms} ms</td>
                    <td className="py-2.5 text-muted-foreground max-w-sm truncate" title={ev.detail}>
                      {ev.detail || '-'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-muted-foreground italic">No telemetry logs found matching filter criteria.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

    </div>
  );
}
