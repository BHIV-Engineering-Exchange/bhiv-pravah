"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DomainStatusRow } from "@/components/DomainStatusRow";
import { EventTimeline } from "@/components/EventTimeline";
import { FileStatusCard } from "@/components/FileStatusCard";
import { HealthBadge } from "@/components/HealthBadge";
import { MetricCard } from "@/components/MetricCard";
import { SectionCard } from "@/components/SectionCard";
import { StatusCard } from "@/components/StatusCard";
import { getAutonomousStatus } from "../services/api";
import {
  getControlPlaneApps,
  getControlPlaneStatus,
  getLiveDashboard,
  getOrchestrationMetrics,
  ingestLink,
  type ControlPlaneApps,
  type ControlPlaneStatus,
  type LivePayload,
  type OrchestrationMetrics,
  removeLink,
} from "../services/api";

export default function HomePage() {
  const [data, setData] = useState<LivePayload | null>(null);
  const [orchestration, setOrchestration] = useState<OrchestrationMetrics | null>(null);
  const [controlPlaneStatus, setControlPlaneStatus] = useState<ControlPlaneStatus | null>(null);
  const [controlPlaneApps, setControlPlaneApps] = useState<ControlPlaneApps | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ingestionLink, setIngestionLink] = useState("");
  const [ingestionError, setIngestionError] = useState<string | null>(null);
  const [isSubmittingLink, setIsSubmittingLink] = useState(false);
  const [autonomousStatus, setAutonomousStatus] = useState<any>(null);

  const telemetry = data?.enhanced_telemetry ?? {
    status: error ? "UNAVAILABLE" : "LOADING",
    avg_latency: "N/A",
    cost: "N/A",
    success: "N/A",
    requests: "N/A"
  };

  async function handleAddLink() {
    if (!ingestionLink.trim()) {
      setIngestionError("Please enter a repository or website link");
      return;
    }

    setIsSubmittingLink(true);
    setIngestionError(null);

    try {
      const result = await ingestLink(ingestionLink.trim());
      if (!result.success) {
        setIngestionError(result.error ?? "Unable to ingest link. Check the URL and try again.");
        return;
      }

      setIngestionLink("");
      const [dashboardPayload, orchestrationPayload, statusPayload, appsPayload] = await Promise.all([
        getLiveDashboard(),
        getOrchestrationMetrics(),
        getControlPlaneStatus(),
        getControlPlaneApps(),
      ]);
      setData(dashboardPayload);
      setOrchestration(orchestrationPayload);
      setControlPlaneStatus(statusPayload);
      setControlPlaneApps(appsPayload);
    } catch {
      setIngestionError("Unable to ingest link. Check the URL and try again.");
    } finally {
      setIsSubmittingLink(false);
    }
  }

  async function handleRemoveLink(link: string) {
    try {
      const result = await removeLink(link);
      if (!result.success) {
        setIngestionError(result.error ?? "Unable to remove link. Try again.");
        return;
      }

      const [dashboardPayload, orchestrationPayload, statusPayload, appsPayload] = await Promise.all([
        getLiveDashboard(),
        getOrchestrationMetrics(),
        getControlPlaneStatus(),
        getControlPlaneApps(),
      ]);
      setData(dashboardPayload);
      setOrchestration(orchestrationPayload);
      setControlPlaneStatus(statusPayload);
      setControlPlaneApps(appsPayload);
    } catch {
      setIngestionError("Unable to remove link. Try again.");
    }
  }

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      try {
        const [dashboardPayload, orchestrationPayload, statusPayload, appsPayload, autonomousPayload] = await Promise.all([
          getLiveDashboard(),
          getOrchestrationMetrics(),
          getControlPlaneStatus(),
          getControlPlaneApps(),
          getAutonomousStatus(),
        ]);
        if (!active) {
          return;
        }
        if (active) {
          setData(dashboardPayload);
          setOrchestration(orchestrationPayload);
          setControlPlaneStatus(statusPayload);
          setControlPlaneApps(appsPayload);
          setError(null);
          setAutonomousStatus(autonomousPayload);
        }
      } catch {
        if (active) {
          setError("Backend dashboard feed unavailable. Ensure backend is running on the configured API port.");
        }
      }
    }

    loadDashboard();

    const interval = window.setInterval(() => {
      void loadDashboard();
    }, 5000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <main className="flex-1 p-6 lg:p-10 relative overflow-hidden animate-fade-in-up">
      {/* Decorative Top Blur */}
      <div className="absolute top-[-10%] right-[-5%] w-[40%] h-[30%] rounded-full bg-sky-600/10 blur-[100px] animate-blob mix-blend-screen pointer-events-none"></div>

      <div className="mx-auto w-full max-w-[1600px] relative z-10 space-y-8">
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10 pb-6 border-b border-slate-800/60">
          <div>
            <h1 className="text-3xl font-display font-extrabold text-slate-100 tracking-tight">Ecosystem Overview</h1>
            <p className="text-slate-400 mt-2 font-medium tracking-wide">Real-time production monitoring and telemetry for all active services.</p>
          </div>
          {error ? (
            <div className="bg-rose-500/10 border border-rose-500/20 px-4 py-2 rounded-lg">
              <p className="text-sm font-semibold text-rose-400">{error}</p>
            </div>
          ) : (
             <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-teal-500/10 border border-teal-500/20">
               <div className="relative flex h-2.5 w-2.5">
                 <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
                 <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-teal-500"></span>
               </div>
               <span className="text-sm font-bold text-teal-400">Live Feed Active</span>
             </div>
          )}
        </header>

        {/* Top Summary Row */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {(data?.summary_metrics ?? []).map((metric) => (
            <MetricCard key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} />
          ))}
        </div>

        <div className="grid gap-8 xl:grid-cols-3">
          {/* Main Content Area */}
          <div className="xl:col-span-2 space-y-8">
            <SectionCard title="Active Microservices">
              <div className="grid gap-6 lg:grid-cols-2">
                {(data?.live_production_monitoring ?? []).map((item) => (
                  <div key={item.name} className="relative">
                    <StatusCard item={item} />
                    {item.domain !== "blackhole.rlreality.ai" && item.domain !== "uni-guru.rlreality.ai" && (
                      <button
                        onClick={() => handleRemoveLink(item.url)}
                        className="absolute right-3 top-3 rounded bg-rose-500/80 px-2 py-1 text-[10px] font-bold text-white uppercase tracking-wider transition hover:bg-rose-600 active:scale-95 shadow-md z-20"
                        aria-label="Remove monitored link"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </SectionCard>

            <SectionCard title="System Performance">
              <div className="grid gap-6 sm:grid-cols-2 md:grid-cols-4">
                {(data?.performance_metrics ?? []).map((metric) => (
                  <MetricCard key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} />
                ))}
              </div>
            </SectionCard>

            <SectionCard title="Infrastructure Health">
              <div className="grid gap-6 sm:grid-cols-2 md:grid-cols-4">
                {(data?.system_health ?? []).map((metric) => (
                  <MetricCard key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} />
                ))}
              </div>
            </SectionCard>
          </div>

          {/* Sidebar Area */}
          <div className="space-y-8">
            <SectionCard title="Ingest New Service">
              <div className="flex flex-col gap-3">
                <input
                  type="url"
                  value={ingestionLink}
                  onChange={(e) => setIngestionLink(e.target.value)}
                  placeholder="Paste URL to monitor..."
                  className="w-full rounded-lg bg-slate-900 border border-slate-700 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 transition-all"
                />
                <button
                  type="button"
                  onClick={handleAddLink}
                  disabled={isSubmittingLink}
                  className="w-full rounded-lg bg-sky-500 hover:bg-sky-400 px-4 py-3 text-sm font-bold text-slate-950 transition-all disabled:opacity-50 shadow-glow-primary"
                >
                  {isSubmittingLink ? "Ingesting..." : "Add to Watchlist"}
                </button>
                {ingestionError && <p className="text-xs font-medium text-rose-400 mt-1">{ingestionError}</p>}
              </div>
            </SectionCard>

            {orchestration && (
              <SectionCard title="Pravah Orchestration">
                <div className="grid gap-4 grid-cols-2">
                  <MetricCard label="RL Brain" value={orchestration.rl_brain.status} tone="green" />
                  <MetricCard label="Control Plane" value={orchestration.control_plane.control_plane_status} tone="green" />
                  <MetricCard label="Decisions" value={String(orchestration.unified.total_decisions_made)} tone="blue" />
                  <MetricCard label="Entities" value={String(orchestration.unified.total_entities_monitored)} tone="blue" />
                </div>
              </SectionCard>
            )}

            <SectionCard title="Autonomous Control">
              {autonomousStatus ? (
                <div className="space-y-4">
                  <MetricCard label="Loop State" value={autonomousStatus.loop_running ? "ACTIVE" : "IDLE"} tone={autonomousStatus.loop_running ? "green" : "orange"} />
                  <MetricCard label="Last Action" value={autonomousStatus.last_action ?? "-"} tone="default" />
                  <MetricCard label="Last Latency" value={String(autonomousStatus.last_runtime?.latency_ms ?? "-") + "ms"} tone="blue" />
                </div>
              ) : (
                <p className="text-sm text-slate-500">Loading autonomous status...</p>
              )}
            </SectionCard>

            <SectionCard title="Telemetry Summary">
              <div className="rounded-xl border border-sky-500/20 bg-sky-500/10 p-6 text-center">
                <p className="text-2xl font-display font-extrabold text-sky-400 shadow-sm">{telemetry.status}</p>
                <div className="mt-4 grid grid-cols-2 gap-2 text-sm font-medium text-sky-200/80">
                  <p className="text-left">Latency:</p> <p className="text-right text-sky-300 font-bold">{telemetry.avg_latency}</p>
                  <p className="text-left">Success:</p> <p className="text-right text-sky-300 font-bold">{telemetry.success}</p>
                  <p className="text-left">Requests:</p> <p className="text-right text-sky-300 font-bold">{telemetry.requests}</p>
                </div>
              </div>
            </SectionCard>
            
            <SectionCard title="Live Events">
              <div className="max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                <EventTimeline events={data?.live_events ?? []} />
              </div>
            </SectionCard>
          </div>
        </div>
      </div>
    </main>
  );
}
