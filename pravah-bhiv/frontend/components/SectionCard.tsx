import type { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  children: ReactNode;
  className?: string;
};

export function SectionCard({ title, children, className = "" }: SectionCardProps) {
  return (
    <section className={`glass-panel p-6 md:p-8 ${className} animate-fade-in-up mb-8`}>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1.5 h-6 bg-sky-500 rounded-full shadow-glow-primary"></div>
        <h2 className="text-xl font-display font-bold text-slate-100 tracking-tight">{title}</h2>
      </div>
      <div>{children}</div>
    </section>
  );
}
