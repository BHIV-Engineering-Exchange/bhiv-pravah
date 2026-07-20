import React, { useState, useEffect, useRef } from "react";
import socket from "../socket/socket";
import { speak } from '../utils/tts';

export default function JobQueuePanel({ jobHistory = [], setJobHistory, engineStatus, lastTelemetry }) {
  const [agentMessage, setAgentMessage] = useState(null);
  const isEngineHealthy = engineStatus?.connected && engineStatus?.healthy;
  const prevJobsRef = useRef({});

  useEffect(() => {
    jobHistory.forEach(job => {
      const prevStatus = prevJobsRef.current[job.id];
      if (prevStatus && prevStatus !== job.status) {
        if (job.status === 'completed') {
          speak('Job completed');
        } else if (job.status === 'failed') {
          speak('Job failed');
        }
      }
      prevJobsRef.current[job.id] = job.status;
    });
  }, [jobHistory]);

  return (
    <div
      className={[
        "relative backdrop-blur-2xl border rounded-3xl overflow-hidden",
        "shadow-[0_18px_45px_rgba(15,23,42,0.6)] transition-all duration-500",
        "bg-gradient-to-br from-slate-50/90 via-white/90 to-sky-50/90",
        "dark:from-slate-950/90 dark:via-slate-900/80 dark:to-slate-950/95",
        "border-slate-200/80 dark:border-slate-800/80",
        "p-6 flex flex-col h-full",
      ].join(" ")}
    >
      <div className="pointer-events-none absolute inset-0 opacity-40 mix-blend-screen">
        <div className="absolute -top-32 -right-16 h-56 w-56 rounded-full bg-sky-500/30 blur-3xl" />
        <div className="absolute -bottom-40 -left-10 h-60 w-60 rounded-full bg-indigo-500/25 blur-3xl" />
      </div>

      <div className="relative mb-4 pb-3 border-b border-slate-200/60 dark:border-white/10">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent tracking-tight">
            World Build Jobs
          </h2>
          <span className="px-3 py-1 text-xs font-semibold rounded-full border backdrop-blur-sm flex items-center gap-1.5 bg-black/5 dark:bg-white/5 text-slate-900 dark:text-slate-100 border-indigo-400/40">
            {jobHistory.length} jobs
          </span>
        </div>
        
        <div className="flex items-center gap-3 text-xs">
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg ${isEngineHealthy ? 'bg-emerald-50/80 dark:bg-emerald-950/50' : 'bg-red-50/80 dark:bg-red-950/50'}`}>
            <span className={`inline-flex h-1.5 w-1.5 rounded-full ${isEngineHealthy ? 'bg-emerald-500 shadow-[0_0_6px_rgba(52,211,153,0.8)]' : 'bg-red-500 animate-pulse shadow-[0_0_6px_rgba(239,68,68,0.8)]'}`} />
            <span className={`font-medium ${isEngineHealthy ? 'text-emerald-700 dark:text-emerald-300' : 'text-red-700 dark:text-red-300'}`}>
              {isEngineHealthy ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          {lastTelemetry && (
            <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
              <span>•</span>
              <span className="font-mono text-[10px]">{new Date(lastTelemetry.timestamp).toLocaleTimeString()}</span>
              <span className="text-[10px] text-sky-600 dark:text-sky-400">({lastTelemetry.event})</span>
            </div>
          )}
        </div>
      </div>

      {jobHistory.length === 0 && (
        <div className="relative flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center justify-center text-center">
            <div className="w-12 h-12 rounded-2xl border border-dashed border-slate-300/70 dark:border-slate-600/70 flex items-center justify-center mb-3 bg-black/5 dark:bg-white/5 backdrop-blur-lg shadow-inner shadow-slate-200/40 dark:shadow-slate-900/60">
              <span className="text-xl">📦</span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400">No jobs yet.</p>
            <p className="text-[11px] mt-1 text-slate-400">Trigger a world build to populate this queue.</p>
          </div>
        </div>
      )}

      {jobHistory.length > 0 && (
        <ul
          className={[
            "relative flex-1 overflow-y-auto rounded-2xl p-3 space-y-1.5",
            "bg-white/70 dark:bg-slate-950/80",
            "border border-slate-200/70 dark:border-slate-800/70",
            "backdrop-blur-xl max-h-[700px]",
            "scrollbar-thin scrollbar-thumb-indigo-500/50 scrollbar-track-slate-200/30",
            "dark:scrollbar-thumb-indigo-400/50 dark:scrollbar-track-slate-800/30",
            "hover:scrollbar-thumb-indigo-600/70 dark:hover:scrollbar-thumb-indigo-300/70",
          ].join(" ")}
          style={{
            scrollbarWidth: 'thin',
            scrollbarColor: 'rgb(99 102 241 / 0.5) rgb(226 232 240 / 0.3)'
          }}
        >
          {jobHistory.map((job) => {
            const statusConfig = {
              completed: {
                text: "text-emerald-600 dark:text-emerald-300",
                dot: "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]",
                bg: "bg-gradient-to-br from-emerald-50/90 to-emerald-100/90 dark:from-emerald-950/40 dark:to-emerald-900/40",
                border: "border-emerald-300/70 dark:border-emerald-700/70",
                accent: "bg-gradient-to-b from-emerald-400 via-emerald-500 to-emerald-600",
                glow: "bg-gradient-to-r from-emerald-500 via-emerald-600 to-emerald-700",
                shadow: "hover:shadow-emerald-500/25"
              },
              failed: {
                text: "text-red-600 dark:text-red-300",
                dot: "bg-red-400 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.6)]",
                bg: "bg-gradient-to-br from-red-50/90 to-red-100/90 dark:from-red-950/40 dark:to-red-900/40",
                border: "border-red-300/70 dark:border-red-700/70",
                accent: "bg-gradient-to-b from-red-500 via-red-600 to-red-700",
                glow: "bg-gradient-to-r from-red-500 via-red-600 to-red-700",
                shadow: "hover:shadow-red-500/25"
              },
              running: {
                text: "text-amber-600 dark:text-amber-300",
                dot: "bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.6)]",
                bg: "bg-gradient-to-br from-amber-50/90 to-amber-100/90 dark:from-amber-950/40 dark:to-amber-900/40",
                border: "border-amber-300/70 dark:border-amber-700/70",
                accent: "bg-gradient-to-b from-amber-400 via-amber-500 to-amber-600",
                glow: "bg-gradient-to-r from-amber-500 via-amber-600 to-amber-700",
                shadow: "hover:shadow-amber-500/25"
              },
              dispatched: {
                text: "text-blue-600 dark:text-blue-300",
                dot: "bg-blue-400 shadow-[0_0_8px_rgba(59,130,246,0.6)]",
                bg: "bg-gradient-to-br from-blue-50/90 to-blue-100/90 dark:from-blue-950/40 dark:to-blue-900/40",
                border: "border-blue-300/70 dark:border-blue-700/70",
                accent: "bg-gradient-to-b from-blue-400 via-blue-500 to-blue-600",
                glow: "bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700",
                shadow: "hover:shadow-blue-500/25"
              },
              queued: {
                text: "text-sky-600 dark:text-sky-300",
                dot: "bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.6)]",
                bg: "bg-gradient-to-br from-sky-50/90 to-sky-100/90 dark:from-sky-950/40 dark:to-sky-900/40",
                border: "border-sky-300/70 dark:border-sky-700/70",
                accent: "bg-gradient-to-b from-sky-400 via-sky-500 to-sky-600",
                glow: "bg-gradient-to-r from-sky-500 via-sky-600 to-sky-700",
                shadow: "hover:shadow-sky-500/25"
              }
            };

            const config = statusConfig[job.status] || statusConfig.queued;

            return (
              <li
                key={job.id}
                className={[
                  "relative flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm group",
                  config.bg,
                  "border",
                  config.border,
                  "text-slate-900 dark:text-slate-100",
                  "transition-all duration-300",
                  "hover:-translate-y-0.5 hover:shadow-lg",
                  config.shadow,
                ].join(" ")}
              >
                <div className={[
                  "absolute inset-y-0 left-0 w-[3px] rounded-l-2xl opacity-80",
                  config.accent
                ].join(" ")} />

                <div className={[
                  "pointer-events-none absolute inset-x-0 top-0 h-[2px] opacity-0 group-hover:opacity-100 transition-opacity duration-300",
                  config.glow
                ].join(" ")} />

                <div className="ml-2 flex-1 min-w-0 flex flex-col gap-1.5">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex h-2 w-2 rounded-full ${config.dot}`} />
                      <span className={`font-bold text-xs ${config.text} uppercase tracking-wide`}>
                        {job.status}
                      </span>
                    </div>
                    <span className="shrink-0 text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                      {new Date(job.submittedAt).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="flex flex-col gap-1">
                    <div className="text-xs">
                      <span className="font-semibold text-slate-700 dark:text-slate-300">Type:</span>{" "}
                      <span className="font-mono text-sky-600 dark:text-sky-300">
                        {job.jobType}
                      </span>
                    </div>

                    {job.retryCount > 0 && job.status !== 'completed' && (
                      <div className="text-[11px] text-amber-600 dark:text-amber-400">
                        Retry {job.retryCount}
                      </div>
                    )}

                    {job.error && (
                      <div className="flex items-start gap-1.5 mt-0.5 p-2 rounded-lg bg-red-100/80 dark:bg-red-950/60 border border-red-300/50 dark:border-red-800/50">
                        <span className="text-red-600 dark:text-red-400 text-xs mt-0.5">⚠️</span>
                        <div className="flex-1 min-w-0">
                          <div className="text-[10px] uppercase tracking-wide text-red-600 dark:text-red-400 font-semibold mb-0.5">Error</div>
                          <div className="font-mono text-xs text-red-700 dark:text-red-300 break-all leading-relaxed">
                            {job.error}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
