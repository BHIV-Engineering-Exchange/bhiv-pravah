import type { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  children: ReactNode;
  className?: string;
};

export function SectionCard({ title, children, className = "" }: SectionCardProps) {
  return (
    <section className={`rounded-3xl bg-slate-900/40 backdrop-blur-xl border border-white/10 p-6 shadow-2xl md:p-8 transition-all duration-500 hover:border-white/20 ${className}`}>
      <h2 className="text-xl font-bold text-slate-100 tracking-tight">{title}</h2>
      <div className="mt-5">{children}</div>
    </section>
  );
}
