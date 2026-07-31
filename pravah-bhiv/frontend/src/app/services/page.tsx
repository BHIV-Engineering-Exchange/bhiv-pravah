'use client';

import React from 'react';
import { useObserverStatus, usePostOverride } from '../../hooks/useBackend';
import { 
  Activity, 
  RefreshCw, 
  HelpCircle, 
  ExternalLink,
  ShieldCheck,
  Zap,
  Server,
  Layers,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';

export default function Services() {
  const { data: observerStatus, isLoading, refetch } = useObserverStatus();
  const postOverride = usePostOverride();

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-20 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <span className="text-xs text-muted-foreground font-mono">LOADING SERVICE TOPOLOGY...</span>
      </div>
    );
  }

  const services = observerStatus ? Object.entries(observerStatus.services).map(([name, info]) => ({
    name,
    ...info,
  })) : [];

  const handleRestart = (name: string) => {
    toast.promise(
      postOverride.mutateAsync({
        app_name: name,
        action: 'clear_freeze'
      }),
      {
        loading: `Sending restart/recovery request for ${name}...`,
        success: `Sent recovery trigger to ${name}`,
        error: `Failed to recover ${name}`
      }
    );
  };

  return (
    <div className="flex-1 flex flex-col gap-6 font-mono text-xs">
      
      {/* Header */}
      <header className="flex justify-between items-end pb-4 border-b border-border/60">
        <div>
          <h2 className="text-xl font-bold font-sans tracking-tight text-foreground flex items-center gap-2">
            <Layers className="w-5 h-5 text-primary" />
            Ecosystem Services
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            View active downstream applications, network URLs, health stats, and connection dependencies
          </p>
        </div>
      </header>

      {/* Services List Table */}
      <section className="premium-card flex flex-col gap-4">
        <div className="flex justify-between items-center border-b border-border/40 pb-2">
          <span className="font-bold text-xs uppercase tracking-wider text-muted-foreground">Ecosystem Components</span>
          <button 
            onClick={() => refetch()}
            className="p-1 hover:text-primary transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[10px] divide-y divide-border">
            <thead>
              <tr className="text-muted-foreground">
                <th className="pb-2 font-medium">Service name</th>
                <th className="pb-2 font-medium">Network Endpoint URL</th>
                <th className="pb-2 font-medium">Latency</th>
                <th className="pb-2 font-medium">Health Status</th>
                <th className="pb-2 font-medium text-right">Intervention</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {services.length > 0 ? (
                services.map((svc, idx) => (
                  <tr key={idx} className="hover:bg-secondary/20 transition-colors">
                    <td className="py-3 font-semibold text-foreground flex items-center gap-1.5 uppercase">
                      <Server className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                      {svc.name}
                    </td>
                    <td className="py-3 text-muted-foreground select-all max-w-[200px] truncate">{svc.url}</td>
                    <td className="py-3 font-semibold text-foreground">{svc.latency_ms} ms</td>
                    <td className="py-3">
                      <span className={`status-pill ${svc.status === 'healthy' ? 'healthy' : (svc.status === 'degraded' ? 'degraded' : 'critical')}`}>
                        {svc.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <button 
                        onClick={() => handleRestart(svc.name)}
                        className="px-2 py-1 bg-secondary hover:bg-border text-foreground hover:text-primary font-sans font-bold text-[9px] rounded transition-colors flex items-center gap-1 ml-auto"
                      >
                        <Zap className="w-2.5 h-2.5" /> Recover
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-muted-foreground italic">
                    No active ecosystem services found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

    </div>
  );
}
