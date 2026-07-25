import { HealthBadge } from "@/components/HealthBadge";

type DomainStatusRowProps = {
  name: string;
  status: string;
};

export function DomainStatusRow({ name, status }: DomainStatusRowProps) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 transition-colors hover:bg-white/10">
      <p className="text-sm font-semibold text-slate-200">{name}</p>
      <HealthBadge status={status} />
    </div>
  );
}
