import React, { useState } from "react";
import socket from "../socket/socket";
import CryptoJS from "crypto-js";

function signAction(type, payload) {
  try {
    const ts = Date.now();
    const nonce = Math.random().toString(36).substring(2, 12);
    const message = `${type}|${JSON.stringify(payload)}|${ts}|${nonce}`;

    const sig = CryptoJS.HmacSHA256(
      message,
      "HMAC_SECRET_987654321"
    ).toString(CryptoJS.enc.Hex);

    return { ts, nonce, sig };
  } catch (err) {
    console.error("[ACTION] Signature generation failed:", err.message);
    throw new Error("Failed to sign action");
  }
}

export default function ActionsPanel({
  compactMode = false,
  soundEnabled = true,
}) {
  const [customAction, setCustomAction] = useState("");

  const sendAction = (type, payload) => {
    const { ts, nonce, sig } = signAction(type, payload);
    socket.emit("action", { type, payload, ts, nonce, sig });
    if (soundEnabled) {
      // playClick();
    }
  };

  const densityBtn = compactMode ? "py-2 px-3 text-sm" : "py-3 px-4";
  const densityWide = compactMode ? "py-2.5 px-4 text-sm" : "py-3 px-6";

  return (
    <div
      className={[
        "relative w-full rounded-3xl",
        "border backdrop-blur-2xl overflow-hidden",
        "shadow-[0_18px_45px_rgba(15,23,42,0.6)] transition-all duration-500",
        "bg-gradient-to-br from-slate-50/90 via-white/90 to-sky-50/90",
        "dark:from-slate-950/90 dark:via-slate-900/80 dark:to-slate-950/95",
        "border-slate-200/80 dark:border-slate-800/80",
        compactMode ? "p-4 max-h-[600px] overflow-y-auto" : "p-6 h-full flex flex-col",
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
              <span className="text-sm">⚡</span>
            </div>
          </div>
          <div>
            <h2 className="text-lg font-semibold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent tracking-tight">
              Quick Actions
            </h2>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Fire signed events to the backend.
            </p>
          </div>
        </div>
      </div>

      {/* Ping */}
      <button
        onClick={() => socket.emit("ping", { message: "frontend ping" })}
        className={[
          "relative w-full mb-4 rounded-2xl border font-medium overflow-hidden group",
          "bg-gradient-to-br from-sky-50/90 to-sky-100/90",
          "dark:from-sky-950/40 dark:to-sky-900/40",
          "border-sky-300/70 dark:border-sky-700/70",
          "text-sky-900 dark:text-sky-100",
          "transition-all flex items-center justify-center gap-2",
          "hover:-translate-y-0.5 hover:shadow-lg hover:shadow-sky-500/25",
          compactMode ? "py-2.5 text-sm" : "py-3",
        ].join(" ")}
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-sky-500 via-blue-500 to-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        🔍 Ping Backend
      </button>

      {/* Actions */}
      <div className={`relative grid ${compactMode ? "grid-cols-1" : "grid-cols-2"} gap-3`}>
        {["inspect", "interact", "speak", "call_npc"].map((type) => (
          <button
            key={type}
            onClick={() =>
              sendAction(type, type === "speak" ? "hello" : null)
            }
            className={[
              "relative rounded-2xl border font-medium overflow-hidden group",
              "bg-gradient-to-br from-white/80 to-slate-100/80",
              "dark:from-slate-900/80 dark:to-slate-800/80",
              "border-slate-200/70 dark:border-slate-700/70",
              "text-slate-900 dark:text-slate-100",
              "transition-all flex items-center justify-center gap-2",
              "hover:-translate-y-0.5 hover:shadow-lg hover:shadow-indigo-500/25 hover:border-indigo-500",
              densityBtn,
            ].join(" ")}
          >
            <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-indigo-500 via-blue-500 to-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            {type.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* Click / Spam */}
      <div className="relative mt-4 space-y-2">
        <button
          onClick={() => sendAction("click", null)}
          className={[
            "relative w-full rounded-2xl border overflow-hidden group",
            "bg-gradient-to-br from-rose-50/90 to-rose-100/90",
            "dark:from-rose-950/40 dark:to-rose-900/40",
            "border-rose-300/70 dark:border-rose-700/70",
            "text-rose-900 dark:text-rose-100",
            "hover:-translate-y-0.5 hover:shadow-lg hover:shadow-rose-500/25",
            "transition-all",
            densityBtn,
          ].join(" ")}
        >
          <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-rose-500 via-red-500 to-orange-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          🖱️ Click
        </button>

        <button
          onClick={() => {
            for (let i = 0; i < 5; i++) {
              setTimeout(() => sendAction("click", null), i * 80);
            }
          }}
          className={[
            "relative w-full rounded-2xl border font-semibold overflow-hidden group",
            "bg-gradient-to-br from-red-50/90 to-red-100/90",
            "dark:from-red-950/40 dark:to-red-900/40",
            "border-red-300/70 dark:border-red-700/70",
            "text-red-900 dark:text-red-100",
            "hover:-translate-y-0.5 hover:shadow-lg hover:shadow-red-500/25",
            "transition-all",
            densityWide,
          ].join(" ")}
        >
          <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-red-500 via-orange-500 to-amber-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          🚀 Spam x5
        </button>
      </div>

      {/* Custom Action */}
      <div className="relative mt-4 flex flex-col gap-2">
        <input
          value={customAction}
          onChange={(e) => setCustomAction(e.target.value)}
          placeholder="Custom action..."
          className={[
            "w-full rounded-2xl px-4 border",
            "bg-white/70 dark:bg-slate-950/80",
            "text-slate-900 dark:text-white",
            "border-slate-200/70 dark:border-slate-800/70",
            "focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20",
            "transition-all",
            compactMode ? "py-2 text-sm" : "py-3",
          ].join(" ")}
        />

        <button
          disabled={!customAction.trim()}
          onClick={() => {
            sendAction(customAction.trim(), null);
            setCustomAction("");
          }}
          className={[
            "relative w-full rounded-2xl font-semibold overflow-hidden group",
            "bg-gradient-to-br from-indigo-500 to-violet-500",
            "text-white shadow-lg shadow-indigo-500/30",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "hover:-translate-y-0.5 hover:shadow-xl hover:shadow-indigo-500/40",
            "transition-all",
            compactMode ? "py-2 text-sm" : "py-3",
          ].join(" ")}
        >
          <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          ⚡ Send
        </button>
      </div>
    </div>
  );
}
