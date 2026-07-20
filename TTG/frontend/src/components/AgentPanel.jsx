// src/components/AgentPanel.jsx
import React from "react";
import { getPresentationalAgent } from "../state/agentsReducer";

export default function AgentPanel({
  agents = {},
  recentEvents = [],
  compactMode = false,
}) {
  const rows = Object.entries(agents);

  return (
    <div
      className={[
        "relative backdrop-blur-2xl border rounded-3xl overflow-hidden",
        "shadow-[0_18px_45px_rgba(15,23,42,0.6)] transition-all duration-500",
        "bg-gradient-to-br from-slate-50/90 via-white/90 to-sky-50/90",
        "dark:from-slate-950/90 dark:via-slate-900/80 dark:to-slate-950/95",
        "border-slate-200/80 dark:border-slate-800/80",
        compactMode ? "p-4" : "p-6",
      ].join(" ")}
      aria-live="polite"
    >
      {/* Ambient glow */}
      <div className="pointer-events-none absolute inset-0 opacity-40 mix-blend-screen">
        <div className="absolute -top-32 -right-16 h-56 w-56 rounded-full bg-sky-500/30 blur-3xl" />
        <div className="absolute -bottom-40 -left-10 h-60 w-60 rounded-full bg-indigo-500/25 blur-3xl" />
      </div>

      {/* Header */}
      <div className="relative flex items-center justify-between mb-4 pb-3 border-b border-slate-200/60 dark:border-white/10">
        <h2 className="text-lg font-semibold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent tracking-tight">
          Agent Status (FSM)
        </h2>

        <span
          className="
            px-3 py-1 text-xs font-semibold rounded-full border backdrop-blur-sm
            flex items-center gap-1
            bg-black/5 dark:bg-white/5
            text-slate-900 dark:text-slate-100
            border-indigo-400/40
          "
        >
          <span className="inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.9)]" />
          {rows.length} agents
        </span>
      </div>

      {/* Empty state */}
      {rows.length === 0 ? (
        <div className="relative flex flex-col items-center justify-center py-10 text-center">
          <div
            className="
              w-12 h-12 rounded-2xl border border-dashed
              border-slate-300/70 dark:border-slate-600/70
              flex items-center justify-center mb-3
              bg-black/5 dark:bg-white/5
              backdrop-blur-lg shadow-inner
              shadow-slate-200/40 dark:shadow-slate-900/60
            "
          >
            <span className="text-xl">🤖</span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No agents registered
          </p>
          <p className="text-[11px] mt-1 text-slate-400">
            Connect an agent to see finite state updates here.
          </p>
        </div>
      ) : (
        <div className="relative flex flex-wrap gap-3">
          {rows.map(([name, rawState]) => {
            const a = getPresentationalAgent(rawState);

            const stateKey = String(a.state).toLowerCase();
            const stateColor =
              {
                idle: "bg-slate-500",
                watching: "bg-sky-500",
                triggered: "bg-rose-500",
                cooldown: "bg-amber-400 text-slate-900",
              }[stateKey] || "bg-slate-400";

            const stateLabel =
              stateKey === "idle"
                ? "Idle"
                : stateKey === "watching"
                ? "Watching"
                : stateKey === "triggered"
                ? "Triggered"
                : stateKey === "cooldown"
                ? "Cooldown"
                : a.state;

            const lastTs = a.ts ? new Date(a.ts).toLocaleTimeString() : "—";

            return (
              <div
                key={name}
                role="region"
                aria-label={`${name} status`}
                className={[
                  "relative w-[320px] rounded-2xl overflow-hidden group",
                  "transition-all duration-500",
                  "bg-gradient-to-br from-white/80 to-slate-100/80",
                  "dark:from-slate-900/80 dark:to-slate-800/80",
                  "border-2",
                  stateKey === "triggered" ? "border-rose-400/70 shadow-lg shadow-rose-500/30" :
                  stateKey === "cooldown" ? "border-amber-400/70 shadow-lg shadow-amber-500/30" :
                  stateKey === "watching" ? "border-sky-400/70 shadow-lg shadow-sky-500/20" :
                  "border-slate-200 dark:border-slate-700/80",
                  "hover:border-indigo-400/70 hover:shadow-indigo-500/25",
                  compactMode ? "p-3" : "p-4",
                  // Scale and glow based on state
                  (stateKey === "triggered" || (stateKey === "cooldown" && a.cooldownPct > 0)) ? "scale-105" : "scale-100",
                ].join(" ")}
              >
                {/* State glow effect */}
                {(stateKey === "triggered" || (stateKey === "cooldown" && a.cooldownPct > 0)) && (
                  <div className="absolute inset-0 pointer-events-none">
                    <div className={[
                      "absolute inset-0 opacity-20 blur-xl",
                      stateKey === "triggered" ? "bg-rose-500" : "bg-amber-500"
                    ].join(" ")} />
                  </div>
                )}
                {/* Header row */}
                <div className="relative flex items-center justify-between mb-2">
                  <div className="font-semibold text-sm text-slate-900 dark:text-slate-100 truncate flex items-center gap-2">
                    <span className={[
                      "text-lg",
                      stateKey === "triggered" ? "animate-pulse" : ""
                    ].join(" ")}>
                      {stateKey === "triggered" ? "⚡" : stateKey === "cooldown" ? "⏳" : stateKey === "watching" ? "👁️" : "💤"}
                    </span>
                    {name}
                  </div>
                  <div
                    className={[
                      "px-2.5 py-1 text-[11px] rounded-full flex items-center gap-1 shadow-sm",
                      stateColor,
                      stateKey === "triggered" || stateKey === "cooldown" ? "animate-pulse" : ""
                    ].join(" ")}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-white/80" />
                    <span className="capitalize font-semibold">{stateLabel}</span>
                  </div>
                </div>

                {/* Meta */}
                <div className="space-y-1 text-[12px] text-slate-700 dark:text-slate-200">
                  <div className="break-words">
                    <span className="text-[10px] uppercase tracking-wide text-indigo-400">
                      Message:
                    </span>{" "}
                    <span className="font-medium">
                      {a.lastMessage || "—"}
                    </span>
                  </div>

                  <div className="break-words">
                    <span className="text-[10px] uppercase tracking-wide text-indigo-400">
                      Reason:
                    </span>{" "}
                    <span className="text-slate-500 dark:text-slate-400">
                      {a.reason || "—"}
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-[11px]">
                    <span className="text-indigo-400 uppercase tracking-wide">
                      Time
                    </span>
                    <span className="font-mono text-[10px]">
                      {lastTs}
                    </span>
                  </div>
                </div>

                {/* Cooldown */}
                <div className="relative mt-3">
                  <div
                    className="
                      h-2 w-full rounded-full overflow-hidden
                      bg-slate-200 dark:bg-slate-900/70
                      border border-slate-300 dark:border-white/5
                    "
                  >
                    <div
                      className="
                        h-full bg-gradient-to-r
                        from-emerald-400 via-cyan-400 to-sky-400
                        transition-[width] duration-300
                      "
                      style={{ width: `${a.cooldownPct || 0}%` }}
                    />
                  </div>

                  <div className="mt-1 flex justify-between text-[10px] text-slate-500 dark:text-slate-400">
                    <span>Cooldown</span>
                    <span className="font-mono">
                      {(a.cooldownPct || 0).toFixed
                        ? a.cooldownPct.toFixed(0)
                        : a.cooldownPct || 0}
                      %
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
