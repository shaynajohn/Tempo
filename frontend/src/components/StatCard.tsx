export function StatCard({
  label,
  value,
  sub,
  accent = "accent",
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: "accent" | "warn" | "danger" | "violet";
}) {
  const accentClass = {
    accent: "from-tempo-accent/20 to-transparent text-tempo-accent",
    warn: "from-tempo-warn/20 to-transparent text-tempo-warn",
    danger: "from-tempo-danger/20 to-transparent text-tempo-danger",
    violet: "from-violet-500/20 to-transparent text-violet-300",
  }[accent];

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.045] p-5 shadow-xl shadow-black/10 backdrop-blur transition duration-300 hover:-translate-y-0.5 hover:border-white/20">
      <div className={`absolute inset-x-0 top-0 h-24 bg-gradient-to-b ${accentClass} opacity-70 transition group-hover:opacity-100`} />
      <div className="relative">
        <div className="mb-4 flex items-center justify-between">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-tempo-muted">
            {label}
          </p>
          <span className={`h-2 w-2 rounded-full ${accentClass.split(" ").at(-1)} bg-current shadow-[0_0_14px_currentColor]`} />
        </div>
        <p className="text-3xl font-semibold tracking-tight tabular-nums">{value}</p>
        {sub && <p className="mt-2 text-xs capitalize text-tempo-muted">{sub}</p>}
      </div>
    </div>
  );
}
