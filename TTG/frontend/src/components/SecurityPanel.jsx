import React from "react";

export default function SecurityPanel({
  agentNonces = {},
  signatureLog = [],
  replayAlerts = [],
  heartbeatStatus = {},
}) {
  return (
    <div
      className={[
        "relative backdrop-blur-2xl border rounded-3xl overflow-hidden",
        "transition-all duration-300",
        // LIGHT
        "bg-white text-slate-900 border-slate-200",
        "shadow-[0_18px_45px_rgba(15,23,42,0.15)]",
        // DARK
        "dark:bg-slate-950 dark:text-slate-100 dark:border-slate-800",
        "dark:shadow-[0_18px_45px_rgba(15,23,42,0.6)]",
        "p-6",
      ].join(" ")}
    >
      {/* Ambient glow */}
      <div className="pointer-events-none absolute inset-0 opacity-30 dark:opacity-40 mix-blend-screen">
        <div className="absolute -top-32 -right-16 h-56 w-56 rounded-full bg-sky-500/20 blur-3xl" />
        <div className="absolute -bottom-40 -left-10 h-60 w-60 rounded-full bg-indigo-500/20 blur-3xl" />
      </div>

      {/* Header */}
      <div className="relative mb-5 pb-3 border-b border-slate-200 dark:border-white/10 flex flex-col items-center gap-1">
        <div className="relative">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-sky-500 via-blue-500 to-indigo-500 shadow-lg" />
          <div className="absolute inset-0 flex items-center justify-center">
            🛡️
          </div>
        </div>

        <h2 className="text-lg font-semibold bg-gradient-to-r from-sky-500 via-blue-500 to-indigo-500 bg-clip-text text-transparent text-center">
          Sovereign Security Indicators
        </h2>

        <p className="text-[11px] text-slate-500 dark:text-slate-400">
          Live integrity and replay-attack signals.
        </p>
      </div>

      <div className="relative space-y-5 text-sm">
        {/* Agent Nonces */}
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide flex items-center gap-1 text-slate-600 dark:text-slate-300">
            🔐 Agent Nonces
          </h3>

          {Object.keys(agentNonces).length === 0 && (
            <p className="text-xs italic text-slate-500">
              No agents registered yet.
            </p>
          )}

          {Object.entries(agentNonces).map(([agent, nonce]) => (
            <div
              key={agent}
              className="flex justify-between items-center py-1.5 border-b border-dashed border-slate-200 dark:border-white/10"
            >
              <span className="truncate">{agent}</span>
              <span className="rounded-xl bg-slate-100 dark:bg-slate-900 px-2.5 py-0.5 font-mono text-[11px] border border-slate-300 dark:border-slate-700">
                {nonce}
              </span>
            </div>
          ))}
        </section>

        {/* Signatures */}
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide flex items-center gap-1 text-slate-600 dark:text-slate-300">
            🖋 Signatures
          </h3>

          {signatureLog.length === 0 ? (
            <p className="text-xs italic text-emerald-600 dark:text-emerald-300/80">
              No signature failures.
            </p>
          ) : (
            <div className="rounded-2xl bg-rose-50 dark:bg-slate-950/70 border border-rose-300 dark:border-rose-500/30 px-3 py-2 space-y-1">
              {signatureLog.slice(0, 5).map((s, i) => (
                <div
                  key={i}
                  className="text-xs text-rose-600 dark:text-rose-300 flex justify-between gap-2 border-b border-dashed border-slate-200 dark:border-white/10 last:border-0 py-1"
                >
                  <span className="font-mono">
                    {new Date(s.ts).toLocaleTimeString()}
                  </span>
                  <span className="text-right">{s.reason}</span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Replay Alerts */}
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide flex items-center gap-1 text-slate-600 dark:text-slate-300">
            ⛔ Replay Alerts
          </h3>

          {replayAlerts.length === 0 ? (
            <p className="text-xs italic text-emerald-600 dark:text-emerald-300/80">
              No replay attacks detected.
            </p>
          ) : (
            <div className="rounded-2xl bg-amber-50 dark:bg-slate-950/70 border border-amber-300 dark:border-amber-400/40 px-3 py-2 space-y-1">
              {replayAlerts.slice(0, 5).map((r, i) => (
                <div
                  key={i}
                  className="text-xs text-amber-600 dark:text-amber-300 flex justify-between gap-2 border-b border-dashed border-slate-200 dark:border-white/10 last:border-0 py-1"
                >
                  <span className="font-mono">
                    {new Date(r.ts).toLocaleTimeString()}
                  </span>
                  <span>Replay detected</span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Heartbeats */}
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide flex items-center gap-1 text-slate-600 dark:text-slate-300">
            💓 Heartbeats
          </h3>

          {Object.keys(heartbeatStatus).length === 0 && (
            <p className="text-xs italic text-slate-500">
              No heartbeat signals yet.
            </p>
          )}

          {Object.entries(heartbeatStatus).map(([agent, hb]) => {
            const text = hb.ok
              ? "text-emerald-600 dark:text-emerald-300"
              : "text-rose-600 dark:text-rose-300";

            return (
              <div
                key={agent}
                className={`flex justify-between items-center py-1.5 text-xs border-b border-dashed border-slate-200 dark:border-white/10 ${text}`}
              >
                <span className="flex items-center gap-1 truncate">
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      hb.ok ? "bg-emerald-400" : "bg-rose-400"
                    }`}
                  />
                  {agent}
                </span>
                <span>
                  {hb.ok ? "OK" : hb.reason} ·{" "}
                  {hb.ts ? new Date(hb.ts).toLocaleTimeString() : "—"}
                </span>
              </div>
            );
          })}
        </section>
      </div>
    </div>
  );
}
