type EventItem = {
  title: string;
  time_ago: string;
  tone: string;
};

type EventTimelineProps = {
  events: EventItem[];
};

const toneClass: Record<string, string> = {
  green: "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)] border-emerald-400",
  blue: "bg-blue-400 shadow-[0_0_10px_rgba(96,165,250,0.8)] border-blue-400",
  indigo: "bg-indigo-400 shadow-[0_0_10px_rgba(129,140,248,0.8)] border-indigo-400",
  orange: "bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.8)] border-amber-400",
  purple: "bg-purple-400 shadow-[0_0_10px_rgba(192,132,252,0.8)] border-purple-400",
  teal: "bg-teal-400 shadow-[0_0_10px_rgba(45,212,191,0.8)] border-teal-400",
  red: "bg-rose-400 shadow-[0_0_10px_rgba(251,113,133,0.8)] border-rose-400"
};

export function EventTimeline({ events }: EventTimelineProps) {
  return (
    <div className="relative pl-6">
      {/* Glowing vertical line */}
      <div className="absolute left-2.5 top-2 bottom-2 w-[2px] bg-gradient-to-b from-violet-500/50 via-fuchsia-500/50 to-transparent shadow-[0_0_8px_rgba(139,92,246,0.5)]"></div>
      
      <ul className="space-y-6">
        {events.map((event, idx) => (
          <li
            key={`${event.title}-${event.time_ago}`}
            className="relative flex items-start group animate-fade-in-up"
            style={{ animationDelay: `${idx * 100}ms` }}
          >
            {/* Glowing Node */}
            <div className={`absolute -left-6 top-1.5 h-3 w-3 rounded-full border-2 border-white/20 z-10 transition-transform group-hover:scale-125 ${toneClass[event.tone] ?? "bg-slate-600 border-slate-600"}`}></div>
            
            <div className="flex-1 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm px-4 py-3 transition-all duration-300 hover:bg-white/10 hover:shadow-glass hover:-translate-y-0.5">
              <p className="text-sm font-semibold text-slate-100 group-hover:text-white transition-colors">🛰️ {event.title}</p>
              <p className="mt-1 text-xs font-medium text-slate-400 group-hover:text-slate-300">{event.time_ago}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
