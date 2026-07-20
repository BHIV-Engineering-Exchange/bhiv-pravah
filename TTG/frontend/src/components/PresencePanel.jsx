import React from "react";
import { Monitor, Smartphone, Tablet, Laptop, Circle } from "lucide-react";
import { speak } from '../utils/tts';

function timeAgo(ts) {
  if (!ts) return "—";
  const diff = Math.floor((Date.now() - ts) / 1000);
  if (diff < 5) return "just now";
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function getDeviceIcon(device) {
  const d = device?.toLowerCase() || "";
  if (d.includes("mobile") || d.includes("phone")) return <Smartphone size={14} />;
  if (d.includes("tablet") || d.includes("ipad")) return <Tablet size={14} />;
  if (d.includes("laptop")) return <Laptop size={14} />;
  return <Monitor size={14} />;
}

export default function PresencePanel({ presenceList = {}, compactMode = false }) {
  const users = Object.values(presenceList);
  const prevUsersRef = React.useRef(users.length);

  React.useEffect(() => {
    if (users.length > prevUsersRef.current) {
      speak('User connected');
    }
    prevUsersRef.current = users.length;
  }, [users.length]);

  return (
    <div
      className={[
        "relative overflow-hidden rounded-3xl border backdrop-blur-2xl",
        "shadow-[0_18px_45px_rgba(15,23,42,0.6)] transition-all duration-500",
        "bg-gradient-to-br from-slate-50/90 via-white/90 to-sky-50/90",
        "dark:from-slate-950/90 dark:via-slate-900/80 dark:to-slate-950/95",
        "border-slate-200/80 dark:border-slate-800/80",
        compactMode ? "p-4" : "p-6",
      ].join(" ")}
    >
      {/* Ambient glow */}
      <div className="pointer-events-none absolute inset-0 opacity-40 mix-blend-screen">
        <div className="absolute -top-32 -right-20 h-56 w-56 rounded-full bg-sky-500/30 blur-3xl" />
        <div className="absolute -bottom-40 -left-10 h-60 w-60 rounded-full bg-indigo-500/25 blur-3xl" />
      </div>

      {/* Header */}
      <div className="relative flex items-center justify-between mb-4 pb-3 border-b border-slate-200/60 dark:border-white/10">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-2xl bg-sky-500/10 border border-sky-400/40 flex items-center justify-center shadow-inner shadow-sky-500/30">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.9)]" />
          </div>
          <h2 className="text-lg font-semibold tracking-tight bg-gradient-to-r from-sky-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent">
            User Presence
          </h2>
        </div>

        <span
          className="
            px-3 py-1 text-xs font-semibold rounded-full border backdrop-blur-md
            flex items-center gap-1
            bg-sky-100/80 dark:bg-sky-500/15
            text-sky-800 dark:text-sky-100
            border-sky-400/70
          "
        >
          <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.9)]" />
          {users.length} online
        </span>
      </div>

      {/* Empty state */}
      {users.length === 0 ? (
        <div className="relative flex flex-col items-center justify-center py-10 text-center">
          <div
            className="
              w-16 h-16 rounded-full border border-dashed
              border-slate-300/70 dark:border-slate-600/70
              flex items-center justify-center mb-3
              bg-black/5 dark:bg-white/5
              backdrop-blur-lg shadow-inner
              shadow-slate-200/40 dark:shadow-slate-900/60
            "
          >
            <Circle size={32} className="text-slate-400 dark:text-slate-500/70" />
          </div>
          <p className="text-slate-500 dark:text-slate-400">
            No users connected
          </p>
          <p className="text-xs mt-1 text-slate-400">
            Waiting for real-time presence signals…
          </p>
        </div>
      ) : (
        <div
          className={`relative max-h-[480px] pr-2 overflow-y-auto ${
            compactMode ? "space-y-3" : "space-y-4"
          }`}
        >
          {users.map((u) => {
            const stateColor =
              u.state === "active"
                ? "bg-emerald-400"
                : u.state === "idle"
                ? "bg-amber-400"
                : "bg-rose-500";

            const roleBadge =
              u.role === "admin"
                ? "bg-gradient-to-br from-violet-500 to-fuchsia-500"
                : "bg-gradient-to-br from-sky-500 to-blue-500";

            return (
              <div
                key={u.userId}
                className={[
                  "relative rounded-2xl border overflow-hidden group",
                  "transition-all duration-300",
                  "bg-gradient-to-br from-white/80 to-slate-100/80",
                  "dark:from-slate-900/80 dark:to-slate-800/80",
                  "border-slate-200 dark:border-slate-700/80",
                  "hover:border-sky-400/70",
                  "hover:shadow-[0_16px_40px_rgba(56,189,248,0.35)]",
                  compactMode ? "p-3.5" : "p-4.5",
                ].join(" ")}
              >
                {/* User row */}
                <div className={`flex items-center gap-4 ${compactMode ? "mb-2" : "mb-3"}`}>
                  <div className="relative w-11 h-11 rounded-2xl flex items-center justify-center font-bold text-white shadow-lg ring-1 ring-sky-400/60">
                    <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-sky-500 via-blue-500 to-indigo-500" />
                    <span className="relative text-xs">
                      {u.userId.slice(0, 2).toUpperCase()}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-sm text-slate-900 dark:text-slate-100 truncate">
                      {u.userId.slice(0, 8)}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                      <span className={`w-2.5 h-2.5 rounded-full ${stateColor}`} />
                      <span className="capitalize">{u.state}</span>
                    </div>
                  </div>
                </div>

                {/* Badges */}
                <div className={`flex flex-wrap gap-2 ${compactMode ? "mb-2" : "mb-3"}`}>
                  <span
                    className={`px-3 py-1 text-[11px] font-semibold rounded-md text-white flex items-center gap-1 ${roleBadge}`}
                  >
                    {u.role === "admin" ? "⭐ admin" : "👤 user"}
                  </span>

                  <span
                    className="
                      px-3 py-1 text-[11px] rounded-md flex items-center gap-1 border
                      bg-slate-100 text-slate-700 border-slate-300
                      dark:bg-slate-900/70 dark:text-slate-200 dark:border-slate-600/80
                    "
                  >
                    {getDeviceIcon(u.device)}
                    <span className="truncate max-w-[140px]">
                      {u.device || "Unknown device"}
                    </span>
                  </span>
                </div>

                {/* Meta */}
                <div
                  className="
                    text-xs flex justify-between items-center rounded-lg px-3 py-2
                    bg-slate-100 border border-slate-200
                    dark:bg-black/30 dark:border-slate-700/70
                  "
                >
                  <span className="text-slate-500 dark:text-slate-400">
                    Last active
                  </span>
                  <span className="font-semibold text-slate-700 dark:text-slate-100">
                    {timeAgo(u.lastActiveAt)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
