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

  // Load full dashboard model from backend.
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
    <main className="min-h-screen px-4 py-8 md:px-8 md:py-12">
      <div className="mx-auto w-full max-w-7xl space-y-8 relative z-10">
        <header className="group relative overflow-hidden rounded-[2.5rem] bg-white/5 border border-white/10 px-6 py-12 text-center shadow-2xl backdrop-blur-xl md:px-12">
          <div className="absolute inset-0 bg-gradient-to-br from-violet-500/5 via-purple-500/5 to-indigo-500/5 opacity-0 transition-opacity duration-700 group-hover:opacity-100"></div>
          <h1 className="relative text-3xl font-extrabold tracking-tight text-white drop-shadow-md md:text-5xl">{data?.header.title ?? "🚀 Pravah Dashboard"}</h1>
          <p className="relative mt-4 text-base font-medium text-slate-300 md:text-lg max-w-2xl mx-auto">{data?.header.subtitle ?? "Real-time Production Monitoring"}</p>
          <div className="relative mt-8 flex justify-center">
            <Link
              href="/decision-brain"
              className="rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 px-6 py-2.5 text-sm font-semibold tracking-wide text-white shadow-lg transition-all hover:scale-105 hover:shadow-violet-500/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
            >
              Open Pravah Control Plane
            </Link>
          </div>
          {error ? <p className="relative mt-4 text-sm font-semibold text-rose-400">{error}</p> : null}
        </header>

        <section className="rounded-3xl bg-white/5 border border-white/10 px-6 py-8 shadow-xl backdrop-blur-lg transition-all hover:bg-white/[0.07] md:px-8">
          <h2 className="text-lg font-bold tracking-tight text-slate-100">📥 Add Repository/Website for Monitoring</h2>
          <div className="mt-5 flex flex-col gap-3 md:flex-row md:gap-3">
            <input
              type="url"
              value={ingestionLink}
              onChange={(e) => setIngestionLink(e.target.value)}
              placeholder="Paste GitHub repo URL, website URL, or API endpoint... (e.g., https://github.com/user/repo)"
              className="flex-1 rounded-xl border border-white/10 bg-black/20 px-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 shadow-inner focus:border-violet-500/50 focus:outline-none focus:ring-2 focus:ring-violet-500/30 transition-all"
            />
            <button
              type="button"
              onClick={handleAddLink}
              disabled={isSubmittingLink}
              suppressHydrationWarning
              className="rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-6 py-2.5 text-sm font-semibold text-white shadow-md transition-all hover:scale-105 hover:shadow-violet-500/30 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 disabled:opacity-50 disabled:hover:scale-100"
            >
              {isSubmittingLink ? "Adding..." : "Add Link"}
            </button>
          </div>
          {ingestionError && <p className="mt-3 text-sm font-medium text-rose-400">{ingestionError}</p>}
          <p className="mt-3 text-xs text-slate-400">Monitoring will automatically update the Live Production Monitoring section below.</p>
        </section>

        <SectionCard title="Live Production Monitoring">
          <div className="grid gap-4 lg:grid-cols-2">
            {(data?.live_production_monitoring ?? []).map((item) => (
              <div key={item.name} className="relative">
                <StatusCard item={item} />
                {item.domain !== "blackhole.rlreality.ai" && item.domain !== "uni-guru.rlreality.ai" && (
                  <button
                    onClick={() => handleRemoveLink(item.url)}
                    className="absolute right-2 top-2 rounded-lg bg-rose-500 px-2 py-1 text-xs font-semibold text-white transition hover:bg-rose-600 active:scale-95"
                    aria-label="Remove monitored link"
                  >
                    ✕ Remove
                  </button>
                )}
              </div>
            ))}
          </div>
        </SectionCard>

        {/* Unified Control Plane Integration Section */}
        {orchestration && (
          <SectionCard title="🌐 Pravah Integration">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <MetricCard label="RL Brain Status" value={orchestration.rl_brain.status} tone="green" />
              <MetricCard label="Control Plane" value={orchestration.control_plane.control_plane_status} tone="green" />
              <MetricCard label="Integration" value={orchestration.unified.integration_enabled ? "Connected" : "Offline"} tone={orchestration.unified.integration_enabled ? "green" : "red"} />
              <MetricCard label="Total Monitored" value={String(orchestration.unified.total_entities_monitored)} tone="blue" />
              <MetricCard label="Decisions Made" value={String(orchestration.unified.total_decisions_made)} tone="blue" />
              <MetricCard label="System Status" value={orchestration.unified.system_status} tone="green" />
              <MetricCard label="CP Availability" value={controlPlaneStatus?.control_plane_available ? "Available" : "Unavailable"} tone={controlPlaneStatus?.control_plane_available ? "green" : "red"} />
              <MetricCard label="Apps Registered" value={String(controlPlaneApps?.total_apps ?? orchestration.control_plane.total_apps_monitored)} tone="blue" />
            </div>
          </SectionCard>
        )}

        <SectionCard title="Summary Metrics">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {(data?.summary_metrics ?? []).map((metric) => (
              <MetricCard key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} />
            ))}
          </div>
        </SectionCard>

        <SectionCard title="AI Learning Status">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            {(data?.ai_learning_status ?? []).map((metric) => (
              <MetricCard key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} />
            ))}
          </div>
        </SectionCard>

        <SectionCard title="System Health">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            {(data?.system_health ?? []).map((metric) => (
              <MetricCard key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} />
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Performance Metrics">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            {(data?.performance_metrics ?? []).map((metric) => (
              <MetricCard key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} />
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Project Files Status">
          <div className="grid gap-4 md:grid-cols-2">
            {(data?.project_files_status ?? []).map((item) => (
              <FileStatusCard
                key={item.title}
                icon={item.icon}
                title={item.title}
                active={item.active}
                total={item.total}
                files={item.files}
              />
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Enhanced Telemetry">
          <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-8 text-center transition-all hover:bg-rose-500/10">
            <p className="text-3xl font-extrabold tracking-widest text-rose-400 drop-shadow-[0_0_10px_rgba(251,113,133,0.3)]">{telemetry.status}</p>
            <div className="mt-4 space-y-1.5 text-sm font-medium text-rose-300/80">
              <p>Avg Latency: <span className="text-rose-200">{telemetry.avg_latency}</span></p>
              <p>Cost: <span className="text-rose-200">{telemetry.cost}</span></p>
              <p>Success: <span className="text-rose-200">{telemetry.success}</span></p>
              <p>Requests: <span className="text-rose-200">{telemetry.requests}</span></p>
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Policy Evolution">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 transition-all hover:bg-white/10">
            <h3 className="text-base font-semibold text-slate-100">{data?.policy_evolution.title ?? "Q-Table Evolution"}</h3>
            <div className="mt-5 grid gap-4 md:grid-cols-3">
              {(data?.policy_evolution.metrics ?? []).map((metric) => (
                <MetricCard key={metric.label} label={metric.label} value={metric.value} />
              ))}
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Error Analytics">
          <div className="grid gap-4 lg:grid-cols-2">
            <article className="rounded-2xl border border-white/10 bg-white/5 p-5 transition-all hover:bg-white/10">
              <h3 className="text-base font-semibold text-slate-100">Recent Errors</h3>
              <ul className="mt-4 space-y-2">
                {(data?.error_analytics.recent_errors ?? []).map((item) => (
                  <li key={item.code} className="flex items-center justify-between rounded-xl border border-white/5 bg-black/20 px-4 py-3 transition-colors hover:bg-white/5">
                    <p className="text-sm font-medium text-slate-200">{item.code}</p>
                    <HealthBadge status={item.severity} />
                  </li>
                ))}
              </ul>
            </article>
            <article className="rounded-2xl border border-white/10 bg-white/5 p-5 transition-all hover:bg-white/10">
              <h3 className="text-base font-semibold text-slate-100">Statistics</h3>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <MetricCard
                  label="Total Errors"
                  value={String(data?.error_analytics.statistics.total_errors ?? 0)}
                  tone="red"
                />
                <MetricCard
                  label="Avg Impact score"
                  value={String(data?.error_analytics.statistics.avg_impact_score ?? 0)}
                  tone="orange"
                />
              </div>
            </article>
          </div>
        </SectionCard>

        <SectionCard title="Auto-Failover Status">
          <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              <MetricCard label="Active Domain" value={data?.auto_failover_status.active_domain ?? "BLACKHOLE"} />
              <MetricCard label="Failure Threshold" value={String(data?.auto_failover_status.failure_threshold ?? 3)} />
            </div>
            <div className="space-y-2">
              {(data?.auto_failover_status.domains ?? []).map((domain) => (
                <DomainStatusRow key={domain.name} name={domain.name} status={domain.status} />
              ))}
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Live Events">
          <EventTimeline events={data?.live_events ?? []} />
        </SectionCard>

        <SectionCard title="🧠 Autonomous Control Loop">
          {autonomousStatus ? (
            <div className="space-y-4">
              <MetricCard label="Loop Running" value={autonomousStatus.loop_running ? "YES" : "NO"} tone="green" />
              <MetricCard label="Last Action" value={autonomousStatus.last_action ?? "-"} />
              <MetricCard label="Last State" value={autonomousStatus.last_runtime?.state ?? "-"} />
              <MetricCard label="Latency (ms)" value={String(autonomousStatus.last_runtime?.latency_ms ?? "-")} />
            </div>
          ) : (
            <p className="text-sm text-slate-500">Loading autonomous status...</p>
          )}
        </SectionCard>


        <footer className="flex justify-center pb-6">
          <Link
            href="/decision-brain"
            className="rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 px-8 py-3 text-sm font-bold tracking-wide text-white shadow-lg transition-all hover:scale-105 hover:shadow-violet-500/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
          >
            Open Pravah Control Plane
          </Link>
        </footer>
      </div>
    </main>
  );
}
