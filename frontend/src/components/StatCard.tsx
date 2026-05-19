export function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-xl border border-tempo-border bg-tempo-surface p-5">
      <p className="text-sm text-tempo-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
      {sub && <p className="mt-1 text-xs text-tempo-muted">{sub}</p>}
    </div>
  );
}
