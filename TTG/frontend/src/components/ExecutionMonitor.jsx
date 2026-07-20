import React, { useState, useEffect } from "react";
import socket from "../socket/socket";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:3000';

export default function ExecutionMonitor() {
  const [executions, setExecutions] = useState([]);
  const [testLoading, setTestLoading] = useState(false);

  const triggerTestExecution = async () => {
    setTestLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/core/test-execution`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      console.log('✓ Test execution triggered:', data);
    } catch (err) {
      console.error('Test failed:', err);
    } finally {
      setTestLoading(false);
    }
  };

  useEffect(() => {
    // Listen for execution updates
    socket.on("execution:started", (data) => {
      setExecutions((prev) => [
        ...prev,
        {
          execution_id: data.execution_id,
          trace_id: data.trace_id,
          status: "running",
          startedAt: Date.now(),
          duration: null,
        },
      ]);
    });

    socket.on("execution:completed", (data) => {
      setExecutions((prev) =>
        prev.map((exec) =>
          exec.execution_id === data.execution_id
            ? {
                ...exec,
                status: "completed",
                duration: data.duration || Date.now() - exec.startedAt,
              }
            : exec
        )
      );
    });

    socket.on("execution:failed", (data) => {
      setExecutions((prev) =>
        prev.map((exec) =>
          exec.execution_id === data.execution_id
            ? {
                ...exec,
                status: "failed",
                duration: Date.now() - exec.startedAt,
                error: data.error,
              }
            : exec
        )
      );
    });

    socket.on("execution:retry", (data) => {
      setExecutions((prev) =>
        prev.map((exec) =>
          exec.execution_id === data.execution_id
            ? { ...exec, status: "retrying", retryCount: data.attempt }
            : exec
        )
      );
    });

    return () => {
      socket.off("execution:started");
      socket.off("execution:completed");
      socket.off("execution:failed");
      socket.off("execution:retry");
    };
  }, []);

  const formatDuration = (ms) => {
    if (!ms) return "-";
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const statusConfig = {
    running: {
      text: "text-amber-600 dark:text-amber-300",
      dot: "bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.6)]",
      bg: "bg-gradient-to-br from-amber-50/90 to-amber-100/90 dark:from-amber-950/40 dark:to-amber-900/40",
      border: "border-amber-300/70 dark:border-amber-700/70",
      accent: "bg-gradient-to-b from-amber-400 via-amber-500 to-amber-600",
    },
    completed: {
      text: "text-emerald-600 dark:text-emerald-300",
      dot: "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]",
      bg: "bg-gradient-to-br from-emerald-50/90 to-emerald-100/90 dark:from-emerald-950/40 dark:to-emerald-900/40",
      border: "border-emerald-300/70 dark:border-emerald-700/70",
      accent: "bg-gradient-to-b from-emerald-400 via-emerald-500 to-emerald-600",
    },
    failed: {
      text: "text-red-600 dark:text-red-300",
      dot: "bg-red-400 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.6)]",
      bg: "bg-gradient-to-br from-red-50/90 to-red-100/90 dark:from-red-950/40 dark:to-red-900/40",
      border: "border-red-300/70 dark:border-red-700/70",
      accent: "bg-gradient-to-b from-red-500 via-red-600 to-red-700",
    },
    retrying: {
      text: "text-blue-600 dark:text-blue-300",
      dot: "bg-blue-400 animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.6)]",
      bg: "bg-gradient-to-br from-blue-50/90 to-blue-100/90 dark:from-blue-950/40 dark:to-blue-900/40",
      border: "border-blue-300/70 dark:border-blue-700/70",
      accent: "bg-gradient-to-b from-blue-400 via-blue-500 to-blue-600",
    },
  };

  return (
    <div className="relative backdrop-blur-2xl border rounded-3xl overflow-hidden shadow-[0_18px_45px_rgba(15,23,42,0.6)] transition-all duration-500 bg-gradient-to-br from-slate-50/90 via-white/90 to-sky-50/90 dark:from-slate-950/90 dark:via-slate-900/80 dark:to-slate-950/95 border-slate-200/80 dark:border-slate-800/80 p-6 flex flex-col h-full">
      <div className="pointer-events-none absolute inset-0 opacity-40 mix-blend-screen">
        <div className="absolute -top-32 -right-16 h-56 w-56 rounded-full bg-purple-500/30 blur-3xl" />
        <div className="absolute -bottom-40 -left-10 h-60 w-60 rounded-full bg-pink-500/25 blur-3xl" />
      </div>

      <div className="relative mb-4 pb-3 border-b border-slate-200/60 dark:border-white/10">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold bg-gradient-to-r from-purple-400 via-pink-400 to-rose-400 bg-clip-text text-transparent tracking-tight">
            Execution Monitor
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={triggerTestExecution}
              disabled={testLoading}
              className="px-3 py-1 text-xs font-semibold rounded-full bg-purple-500 text-white hover:bg-purple-600 disabled:opacity-50 transition-all"
            >
              {testLoading ? '⏳ Testing...' : '🧪 Test'}
            </button>
            <span className="px-3 py-1 text-xs font-semibold rounded-full border backdrop-blur-sm flex items-center gap-1.5 bg-black/5 dark:bg-white/5 text-slate-900 dark:text-slate-100 border-purple-400/40">
              {executions.length} executions
            </span>
          </div>
        </div>
      </div>

      {executions.length === 0 && (
        <div className="relative flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center justify-center text-center">
            <div className="w-12 h-12 rounded-2xl border border-dashed border-slate-300/70 dark:border-slate-600/70 flex items-center justify-center mb-3 bg-black/5 dark:bg-white/5 backdrop-blur-lg shadow-inner shadow-slate-200/40 dark:shadow-slate-900/60">
              <span className="text-xl">⚡</span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400">No executions yet.</p>
            <p className="text-[11px] mt-1 text-slate-400">Start an execution to see it here.</p>
          </div>
        </div>
      )}

      {executions.length > 0 && (
        <ul className="relative flex-1 overflow-y-auto rounded-2xl p-3 space-y-2 bg-white/70 dark:bg-slate-950/80 border border-slate-200/70 dark:border-slate-800/70 backdrop-blur-xl max-h-[700px] scrollbar-thin scrollbar-thumb-purple-500/50 scrollbar-track-slate-200/30 dark:scrollbar-thumb-purple-400/50 dark:scrollbar-track-slate-800/30">
          {executions.map((exec) => {
            const config = statusConfig[exec.status] || statusConfig.running;

            return (
              <li
                key={exec.execution_id}
                className={`relative flex flex-col gap-2 rounded-2xl px-4 py-3 text-sm group ${config.bg} border ${config.border} transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg`}
              >
                <div className={`absolute inset-y-0 left-0 w-[3px] rounded-l-2xl opacity-80 ${config.accent}`} />

                <div className="ml-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex h-2 w-2 rounded-full ${config.dot}`} />
                    <span className={`font-bold text-xs ${config.text} uppercase tracking-wide`}>
                      {exec.status}
                    </span>
                    {exec.retryCount > 0 && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-300">
                        Retry {exec.retryCount}
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-mono text-slate-600 dark:text-slate-400">
                    {formatDuration(exec.duration || Date.now() - exec.startedAt)}
                  </span>
                </div>

                <div className="ml-2 flex flex-col gap-1">
                  <div className="text-xs">
                    <span className="font-semibold text-slate-700 dark:text-slate-300">ID:</span>{" "}
                    <span className="font-mono text-purple-600 dark:text-purple-300 text-[11px]">
                      {exec.execution_id}
                    </span>
                  </div>

                  {exec.trace_id && (
                    <div className="text-xs">
                      <span className="font-semibold text-slate-700 dark:text-slate-300">Trace:</span>{" "}
                      <span className="font-mono text-slate-500 dark:text-slate-400 text-[10px]">
                        {exec.trace_id}
                      </span>
                    </div>
                  )}

                  {exec.error && (
                    <div className="mt-1 p-2 rounded-lg bg-red-100/80 dark:bg-red-950/60 border border-red-300/50 dark:border-red-800/50">
                      <div className="text-[10px] uppercase tracking-wide text-red-600 dark:text-red-400 font-semibold mb-0.5">
                        Error
                      </div>
                      <div className="font-mono text-xs text-red-700 dark:text-red-300 break-all">
                        {exec.error}
                      </div>
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
