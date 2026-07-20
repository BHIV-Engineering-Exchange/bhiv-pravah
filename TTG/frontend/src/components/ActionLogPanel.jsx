import React from "react";

export default function ActionLogPanel({ actionLog = [] }) {
  const getUserId = (a) => {
    if (typeof a.userId === "string") return a.userId;
    if (a.userId?.userId) return a.userId.userId;
    return "system";
  };

  const isEmpty = !actionLog || actionLog.length === 0;

  return (
    <div
      className={[
        "relative backdrop-blur-2xl border rounded-3xl overflow-hidden",
        "shadow-[0_18px_45px_rgba(15,23,42,0.6)] transition-all duration-500",
        "bg-gradient-to-br from-slate-50/90 via-white/90 to-sky-50/90",
        "dark:from-slate-950/90 dark:via-slate-900/80 dark:to-slate-950/95",
        "border-slate-200/80 dark:border-slate-800/80",
        "p-6",
      ].join(" ")}
    >
      {/* Ambient glow */}
      <div className="pointer-events-none absolute inset-0 opacity-40 mix-blend-screen">
        <div className="absolute -top-32 -right-16 h-56 w-56 rounded-full bg-sky-500/30 blur-3xl" />
        <div className="absolute -bottom-40 -left-10 h-60 w-60 rounded-full bg-indigo-500/25 blur-3xl" />
      </div>

      {/* Header */}
      <div className="relative flex items-center justify-between mb-4 pb-3 border-b border-slate-200/60 dark:border-white/10">
        <div className="flex items-center gap-2">
          <div className="relative">
            <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-sky-500 via-blue-500 to-indigo-500 shadow-lg shadow-sky-500/40 ring-1 ring-sky-400/70" />
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-sm">📝</span>
            </div>
          </div>
          <h2 className="text-lg font-semibold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent tracking-tight">
            Action Log
          </h2>
        </div>

        <span className="px-3 py-1 text-xs font-semibold rounded-full
                         bg-black/5 dark:bg-white/5
                         text-slate-900 dark:text-slate-100
                         border border-indigo-400/40 backdrop-blur-sm flex items-center gap-1">
          <span className="inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.9)]" />
          {actionLog.length} events
        </span>
      </div>

      {/* Empty state */}
      {isEmpty && (
        <div className="relative flex flex-col items-center justify-center py-10 text-center
                        text-slate-500 dark:text-slate-400">
          <div className="w-12 h-12 rounded-2xl border border-dashed
                          border-slate-300/70 dark:border-slate-600/70
                          flex items-center justify-center mb-3
                          bg-black/5 dark:bg-white/5
                          backdrop-blur-lg shadow-inner
                          shadow-slate-200/40 dark:shadow-slate-900/60">
            <span className="text-xl">📝</span>
          </div>
          <p className="text-sm">No actions yet</p>
          <p className="text-[11px] mt-1 opacity-70">
            Interact with the <strong>system</strong> to populate the log.
          </p>
        </div>
      )}

      {/* Log list */}
      {!isEmpty && (
        <div
          className={[
            "relative mt-3 max-h-[400px] overflow-y-auto rounded-2xl p-3 space-y-2",
            "bg-white/70 dark:bg-slate-950/80",
            "border border-slate-200/70 dark:border-slate-800/70",
            "backdrop-blur-xl",
          ].join(" ")}
        >
          {actionLog.map((a) => {
            const isError = a.category === "error" || a.type === "error";
            const isSystem = getUserId(a) === "system";

            const accentBar = isError
              ? "from-rose-500 to-orange-400"
              : isSystem
              ? "from-sky-400 to-indigo-400"
              : "from-emerald-400 to-indigo-400";

            return (
              <div
                key={a._id || `${a.sessionId}-${a.clientTs}`}
                className={[
                  "relative rounded-2xl px-3 py-2.5 text-sm group",
                  "bg-gradient-to-br from-white/80 to-slate-100/80",
                  "dark:from-slate-900/80 dark:to-slate-800/80",
                  "border border-slate-200/70 dark:border-slate-700/70",
                  "text-slate-900 dark:text-slate-100",
                  "transition-all duration-300",
                  "hover:-translate-y-0.5 hover:border-indigo-500",
                  "hover:shadow-lg hover:shadow-indigo-500/25",
                ].join(" ")}
              >
                {/* Accent line */}
                <div
                  className={`absolute inset-y-0 left-0 w-[3px]
                              bg-gradient-to-b ${accentBar}
                              rounded-l-2xl opacity-80`}
                />

                {/* Hover glow */}
                <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px]
                                bg-gradient-to-r from-indigo-500 via-blue-500 to-cyan-400
                                opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                <div className="ml-2">
                  {/* Header row */}
                  <div className="flex items-center justify-between">
                    <div className="font-semibold flex items-center gap-2">
                      <span className="uppercase tracking-wide text-xs
                                       text-slate-700 dark:text-indigo-300">
                        {a.type}
                      </span>
                      <span className="text-[11px] px-2 py-0.5 rounded-full
                                       bg-black/10 dark:bg-white/10
                                       text-slate-700 dark:text-indigo-200
                                       border border-indigo-500/40">
                        {a.category || "uncategorized"}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-500 dark:text-slate-400">
                      {new Date(a.serverTs || a.clientTs).toLocaleTimeString()}
                    </span>
                  </div>

                  {/* Meta */}
                  <div className="mt-2 flex flex-wrap gap-3 text-[11px]
                                  text-slate-500 dark:text-slate-400">
                    <span className="inline-flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      User:
                      <span className="font-mono text-slate-900 dark:text-slate-200">
                        {getUserId(a).slice(0, 6)}
                      </span>
                    </span>

                    <span className="inline-flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
                      Session:
                      <span className="font-mono text-slate-900 dark:text-slate-200">
                        {a.sessionId ? a.sessionId.split(":")[1] : "—"}
                      </span>
                    </span>

                    {a.payload && (
                      <span className="inline-flex items-center gap-1 opacity-80">
                        <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                        Payload
                      </span>
                    )}
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
