import { HealthBadge } from "@/components/HealthBadge";

type FileRow = {
  filename: string;
  status: string;
  size: string;
};

type FileStatusCardProps = {
  icon: string;
  title: string;
  active: number;
  total: number;
  files: FileRow[];
};

export function FileStatusCard({ icon, title, active, total, files }: FileStatusCardProps) {
  return (
    <article className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md p-5 shadow-lg transition-all duration-300 hover:bg-white/10">
      <div className="flex items-center gap-3">
        <span aria-hidden="true" className="text-xl drop-shadow-md">{icon}</span>
        <h3 className="text-base font-semibold text-slate-100 tracking-tight">{title}</h3>
      </div>
      <p className="mt-2 text-sm text-slate-400">{active} / {total} files active</p>

      <div className="mt-5 max-h-44 space-y-3 overflow-y-auto pr-2 custom-scrollbar">
        {files.map((file) => (
          <div key={file.filename} className="rounded-xl border border-white/5 bg-white/5 px-4 py-3 transition-colors hover:bg-white/10">
            <div className="flex items-center justify-between gap-3">
              <p className="truncate text-xs font-medium text-slate-200">{file.filename}</p>
              <HealthBadge status={file.status} />
            </div>
            <p className="mt-1.5 text-xs text-slate-500">Size: {file.size}</p>
          </div>
        ))}
      </div>
    </article>
  );
}
