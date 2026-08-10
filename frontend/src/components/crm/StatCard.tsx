type StatCardProps = {
  title: string;
  value: string;
  hint?: string;
};

export function StatCard({ title, value, hint }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-sm shadow-slate-950/20">
      <p className="text-xs uppercase tracking-[0.14em] text-slate-400">{title}</p>
      <div className="mt-3 flex items-end justify-between gap-3">
        <h3 className="text-2xl font-bold text-white">{value}</h3>
        {hint ? <span className="text-xs text-indigo-300">{hint}</span> : null}
      </div>
    </div>
  );
}
