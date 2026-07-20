import React, { useState, useEffect } from "react";
import useTheme from "../hooks/useTheme";

export default function UserPreferencePanel() {
  // global theme (correct)
  const { theme, setTheme } = useTheme();
  const darkMode = theme === "dark";

  // local preferences (correct)
  const [compactMode, setCompactMode] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [language, setLanguage] = useState('en');

  useEffect(() => {
    const savedCompact = localStorage.getItem("pref_compact") === "true";
    const savedSound = localStorage.getItem("pref_sound") !== "false";
    const savedLanguage = localStorage.getItem("pref_language");

    setCompactMode(savedCompact);
    setSoundEnabled(savedSound);
    
    if (!savedLanguage) {
      localStorage.setItem("pref_language", "en");
      setLanguage("en");
    } else {
      setLanguage(savedLanguage);
    }

    applyDensity(savedCompact);
  }, []);

  const applyDensity = (isCompact) => {
    const app = document.querySelector(".app-root");
    if (!app) return;
    app.classList.toggle("compact", isCompact);
  };

  const toggleCompact = () => {
    const next = !compactMode;
    setCompactMode(next);
    localStorage.setItem("pref_compact", next);
    applyDensity(next);
  };

  const toggleSound = () => {
    const next = !soundEnabled;
    setSoundEnabled(next);
    localStorage.setItem("pref_sound", next);
  };

  const toggleTheme = () => {
    setTheme(darkMode ? "light" : "dark");
  };

  const handleLanguageChange = (e) => {
    const newLang = e.target.value;
    setLanguage(newLang);
    localStorage.setItem("pref_language", newLang);
    window.dispatchEvent(new Event('storage'));
  };

  const labelMuted = darkMode ? "text-slate-400" : "text-slate-500";

  return (
    <div
      className={[
        "relative max-w-sm mx-auto rounded-3xl border backdrop-blur-2xl",
        "shadow-[0_18px_45px_rgba(15,23,42,0.6)] transition-all duration-500",
        "overflow-hidden",
        darkMode
          ? "bg-gradient-to-br from-slate-950/90 via-slate-900/80 to-slate-950/95 border-slate-800/80 hover:border-sky-400/70 hover:shadow-[0_22px_60px_rgba(56,189,248,0.35)]"
          : "bg-gradient-to-br from-slate-50/90 via-white/90 to-sky-50/90 border-slate-200/80 hover:border-sky-400/70 hover:shadow-[0_16px_45px_rgba(56,189,248,0.35)]",
        "p-6",
      ].join(" ")}
    >
      {/* Ambient glow */}
      <div className="pointer-events-none absolute inset-0 opacity-40 mix-blend-screen">
        <div className="absolute -top-32 -right-16 h-56 w-56 rounded-full bg-sky-500/30 blur-3xl" />
        <div className="absolute -bottom-40 -left-10 h-60 w-60 rounded-full bg-indigo-500/25 blur-3xl" />
      </div>

      {/* Header */}
      <div className="relative mb-6 flex flex-col items-center">
        <div className="relative mb-4">
          <div className="w-14 h-14 rounded-3xl bg-gradient-to-br from-sky-500 via-blue-500 to-indigo-500 shadow-lg shadow-sky-500/40 ring-1 ring-sky-400/70" />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xl">⚙️</span>
          </div>
        </div>
        <h2 className="text-xl font-semibold bg-gradient-to-r from-sky-300 via-blue-300 to-indigo-300 bg-clip-text text-transparent tracking-tight">
          User Preferences
        </h2>
        <p className={`mt-1 text-xs ${labelMuted}`}>
          Tune your <strong>experience</strong> in real time.
        </p>
      </div>

      {/* Toggles */}
      <div className="relative space-y-4">
        {/* Compact Mode */}
        <label className="flex items-center justify-between p-4 rounded-2xl border bg-white/5 hover:bg-white/10 backdrop-blur-sm border-white/10 hover:border-sky-400/40 hover:shadow-md hover:shadow-sky-500/20 transition-all duration-300 group cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-400/30 to-cyan-400/30 border border-blue-400/40 shadow-md shadow-blue-500/30 flex items-center justify-center group-hover:scale-110 transition-transform">
              <span className="text-blue-200 text-lg">📦</span>
            </div>
            <div>
              <div className="font-medium text-slate-50 group-hover:text-sky-200 transition-colors text-sm">
                Compact Layout
              </div>
              <div className="text-xs text-slate-400 group-hover:text-slate-200">
                Reduced spacing, more density
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={toggleCompact}
            className={[
              "relative inline-flex h-6 w-11 items-center rounded-full border transition-all duration-300",
              compactMode
                ? "bg-emerald-400/90 border-emerald-300 shadow-[0_0_16px_rgba(52,211,153,0.9)]"
                : "bg-slate-900/50 border-slate-600",
            ].join(" ")}
          >
            <span
              className={[
                "inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform duration-300",
                compactMode ? "translate-x-5" : "translate-x-1",
              ].join(" ")}
            />
          </button>
        </label>

        {/* Dark Mode */}
        <label className="flex items-center justify-between p-4 rounded-2xl border bg-white/5 hover:bg-white/10 backdrop-blur-sm border-white/10 hover:border-purple-400/40 hover:shadow-md hover:shadow-purple-500/20 transition-all duration-300 group cursor-pointer">
          <div className="flex items-center gap-3">
            <div
              className={[
                "w-10 h-10 rounded-2xl backdrop-blur-sm border shadow-md flex items-center justify-center group-hover:scale-110 transition-all duration-300",
                darkMode
                  ? "bg-gradient-to-br from-slate-700/60 to-slate-900/70 border-purple-400/40 shadow-purple-500/30"
                  : "bg-gradient-to-br from-orange-400/40 to-yellow-400/40 border-orange-400/40 shadow-orange-500/30",
              ].join(" ")}
            >
              <span
                className={[
                  "text-lg",
                  darkMode ? "text-purple-200" : "text-orange-200",
                ].join(" ")}
              >
                {darkMode ? "🌙" : "☀️"}
              </span>
            </div>
            <div>
              <div className="font-medium text-slate-50 group-hover:text-purple-200 transition-colors text-sm">
                Dark Mode
              </div>
              <div className="text-xs text-slate-400 group-hover:text-slate-200">
                Eye-friendly, contrast-rich UI
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={toggleTheme}
            className={[
              "relative inline-flex h-6 w-11 items-center rounded-full border transition-all duration-300",
              darkMode
                ? "bg-purple-500/90 border-purple-300 shadow-[0_0_16px_rgba(168,85,247,0.85)]"
                : "bg-slate-900/50 border-slate-600",
            ].join(" ")}
          >
            <span
              className={[
                "inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform duration-300",
                darkMode ? "translate-x-5" : "translate-x-1",
              ].join(" ")}
            />
          </button>
        </label>

        {/* Language Selection */}
        <div className="p-4 rounded-2xl border bg-white/5 hover:bg-white/10 backdrop-blur-sm border-white/10 hover:border-indigo-400/40 hover:shadow-md hover:shadow-indigo-500/20 transition-all duration-300 group">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-400/30 to-purple-400/30 border border-indigo-400/40 shadow-md shadow-indigo-500/30 flex items-center justify-center group-hover:scale-110 transition-transform">
              <span className="text-indigo-200 text-lg">🌐</span>
            </div>
            <div>
              <div className="font-medium text-slate-50 group-hover:text-indigo-200 transition-colors text-sm">Language</div>
              <div className="text-xs text-slate-400 group-hover:text-slate-200">Select interface language</div>
            </div>
          </div>
          <div className="relative">
            <select
              value={language}
              onChange={handleLanguageChange}
              className={[
                "w-full px-4 py-3 rounded-xl border transition-all duration-300 appearance-none",
                "bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-sm",
                "border-slate-600/50 text-slate-100 font-medium",
                "hover:border-indigo-400/70 hover:shadow-lg hover:shadow-indigo-500/20",
                "focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/40 focus:shadow-xl focus:shadow-indigo-500/30",
                "outline-none cursor-pointer pr-10",
                "hover:scale-[1.02] active:scale-[0.98]"
              ].join(" ")}
            >
              <option value="en" className="bg-slate-900 text-slate-100 py-2">🇬🇧 English</option>
              <option value="es" className="bg-slate-900 text-slate-100 py-2">🇪🇸 Español</option>
              <option value="fr" className="bg-slate-900 text-slate-100 py-2">🇫🇷 Français</option>
              <option value="de" className="bg-slate-900 text-slate-100 py-2">🇩🇪 Deutsch</option>
              <option value="it" className="bg-slate-900 text-slate-100 py-2">🇮🇹 Italiano</option>
              <option value="pt" className="bg-slate-900 text-slate-100 py-2">🇵🇹 Português</option>
              <option value="ru" className="bg-slate-900 text-slate-100 py-2">🇷🇺 Русский</option>
              <option value="zh" className="bg-slate-900 text-slate-100 py-2">🇨🇳 中文</option>
              <option value="ja" className="bg-slate-900 text-slate-100 py-2">🇯🇵 日本語</option>
              <option value="ko" className="bg-slate-900 text-slate-100 py-2">🇰🇷 한국어</option>
              <option value="hi" className="bg-slate-900 text-slate-100 py-2">🇮🇳 हिन्दी</option>
              <option value="ar" className="bg-slate-900 text-slate-100 py-2">🇸🇦 العربية</option>
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
              <svg className="w-5 h-5 text-indigo-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Status row */}
      <div className="relative mt-6 pt-5 border-t border-white/10">
        <div className="flex flex-wrap items-center justify-center gap-3 text-[11px]">
          <span
            className={[
              "px-3 py-1 rounded-full bg-white/5 backdrop-blur-sm border",
              compactMode
                ? "border-emerald-400/40 text-emerald-300"
                : "border-slate-500/40 text-slate-300",
            ].join(" ")}
          >
            {compactMode ? "Compact ON" : "Compact OFF"}
          </span>
          <span
            className={[
              "px-3 py-1 rounded-full bg-white/5 backdrop-blur-sm border",
              darkMode
                ? "border-purple-400/40 text-purple-300"
                : "border-orange-400/40 text-orange-300",
            ].join(" ")}
          >
            {darkMode ? "🌙 Dark" : "☀️ Light"}
          </span>
          <span className="px-3 py-1 rounded-full bg-white/5 backdrop-blur-sm border border-indigo-400/40 text-indigo-300">
            🌐 {language.toUpperCase()}
          </span>
        </div>
      </div>
    </div>
  );
}
