"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { name: "Live Ecosystem", path: "/", icon: "🌐" },
  { name: "Control Plane", path: "/decision-brain", icon: "🧠" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 w-64 bg-slate-900/80 backdrop-blur-2xl border-r border-slate-700/50 z-50 flex flex-col hidden lg:flex shadow-2xl">
      <div className="p-6 border-b border-slate-800/60">
        <h1 className="text-2xl font-display font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-teal-400 drop-shadow-sm">
          Pravah <span className="font-light text-slate-400">Bhiv</span>
        </h1>
        <p className="text-xs font-medium text-slate-500 mt-1 uppercase tracking-widest">Enterprise Command</p>
      </div>
      
      <nav className="flex-1 py-6 px-4 space-y-2">
        {navItems.map((item) => {
          const isActive = pathname === item.path;
          return (
            <Link
              key={item.path}
              href={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 font-medium text-sm ${
                isActive 
                  ? "bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-[0_0_15px_rgba(14,165,233,0.1)]" 
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-6 border-t border-slate-800/60">
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-950/50 border border-slate-800/50">
          <div className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </div>
          <span className="text-xs font-bold text-slate-300">System Secure</span>
        </div>
      </div>
    </aside>
  );
}
