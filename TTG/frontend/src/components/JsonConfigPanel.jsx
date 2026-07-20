import React, { useState } from "react";
import socket from "../socket/socket";
import CubePreview from "./CubePreview";

export default function JsonConfigPanel({ onConfigChange, previewConfig }) {
  const [jsonText, setJsonText] = useState(
    '{"color": "#66ffdd", "size": 1}'
  );
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);

  const handlePreview = () => {
    try {
      const parsed = JSON.parse(jsonText);
      setError(null);
      
      if (parsed.color && parsed.size) {
        const hexToRgb = (hex) => {
          const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
          return result ? [
            parseInt(result[1], 16) / 255,
            parseInt(result[2], 16) / 255,
            parseInt(result[3], 16) / 255
          ] : [1, 1, 1];
        };
        
        onConfigChange({
          color: hexToRgb(parsed.color),
          size: parsed.size
        });
      }
    } catch (e) {
      setError("Invalid JSON: " + e.message);
    }
  };

  // REMOVED Day 9: Generate World button
  // All execution must go through /core/execute with security enforcement
  // const handleGenerate = () => { ... }

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
      <div className="relative mb-4 pb-3 border-b border-slate-200/60 dark:border-white/10">
        <h2 className="text-lg font-semibold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent tracking-tight">
          Cube Config (JSON)
        </h2>
      </div>

      {/* JSON textarea */}
      <textarea
        rows={4}
        value={jsonText}
        onChange={(e) => setJsonText(e.target.value)}
        className={[
          "w-full mb-3 rounded-2xl p-3 font-mono text-sm resize-y shadow-inner",
          "bg-white/80 text-slate-800 border border-slate-300/70",
          "dark:bg-slate-950/75 dark:text-cyan-300 dark:border-slate-700/80",
          "focus:outline-none focus:ring-2 focus:ring-cyan-400/40 focus:border-cyan-300/50",
        ].join(" ")}
      />

      {/* Preview button */}
      <div className="flex gap-2 mb-3">
        <button
          onClick={handlePreview}
          className={[
            "flex-1 rounded-2xl px-4 py-2.5 text-sm font-medium",
            "bg-gradient-to-r from-slate-200 to-slate-300",
            "dark:from-slate-800/80 dark:to-slate-900/80",
            "border border-slate-300 dark:border-slate-600/80",
            "text-slate-800 dark:text-sky-200",
            "shadow-md hover:shadow-lg",
            "hover:border-sky-400/60 hover:scale-[1.02] hover:-translate-y-0.5",
            "transition-all duration-300 flex items-center justify-center gap-2",
          ].join(" ")}
        >
          <span>👁️</span>
          <span>Preview Cube</span>
        </button>
      </div>

      {/* Cube preview */}
      <div
        className="
          rounded-2xl border p-3 mb-3 backdrop-blur-xl
          bg-white/70 border-slate-200
          dark:bg-slate-950/70 dark:border-slate-800/80
        "
      >
        <CubePreview config={previewConfig} />
      </div>

      {/* REMOVED Day 9: Generate World button - use /core/execute instead */}
      {/* <button onClick={handleGenerate}>Generate World</button> */}

      {/* Error */}
      {error && (
        <div className="mt-3 text-sm text-pink-600 dark:text-pink-400 bg-pink-500/5 border border-pink-500/40 rounded-2xl px-3 py-2">
          {error}
        </div>
      )}

      {/* Hint */}
      <div className="mt-3 text-xs text-slate-500 dark:text-slate-400">
        Example:{" "}
        <code
          className="
            font-mono text-[11px] px-2 py-1 rounded-xl border
            bg-slate-100 text-slate-800 border-slate-300
            dark:bg-slate-900/70 dark:text-cyan-300 dark:border-slate-700/70
          "
        >
          {'{ "color": "#B6FF00", "size": 1.3 }'}
        </code>
      </div>
    </div>
  );
}
