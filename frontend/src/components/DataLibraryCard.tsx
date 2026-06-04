import Link from "next/link";
import type { LibraryStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

const tone: Record<LibraryStatus["freshness"], string> = {
  empty: "border-tempo-border bg-tempo-surface text-tempo-muted",
  fresh: "border-tempo-accent/40 bg-tempo-accent/5 text-tempo-accent",
  aging: "border-tempo-warn/40 bg-tempo-warn/5 text-tempo-warn",
  stale: "border-tempo-danger/40 bg-tempo-danger/5 text-tempo-danger",
};

export function DataLibraryCard({ status }: { status: LibraryStatus }) {
  return (
    <section className="rounded-xl border border-tempo-border bg-tempo-surface p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-medium">Data library</h2>
            <span
              className={cn(
                "rounded-full border px-2 py-0.5 text-xs capitalize",
                tone[status.freshness]
              )}
            >
              {status.freshness}
            </span>
          </div>
          <p className="mt-2 text-sm text-tempo-muted">{status.summary}</p>
        </div>
        {status.needs_import && (
          <Link
            href="/import"
            className="rounded-lg bg-tempo-accent px-4 py-2 text-sm font-medium text-tempo-bg hover:opacity-90"
          >
            Refresh data
          </Link>
        )}
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MiniStat label="Runs stored" value={String(status.activity_count)} />
        <MiniStat label="Wellness days" value={String(status.wellness_count)} />
        <MiniStat
          label="Latest run"
          value={formatDate(status.latest_activity_date)}
        />
        <MiniStat
          label="Latest wellness"
          value={formatDate(status.latest_wellness_date)}
        />
      </div>
    </section>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-tempo-border bg-tempo-bg/40 px-3 py-2">
      <p className="text-xs text-tempo-muted">{label}</p>
      <p className="mt-0.5 font-medium tabular-nums">{value}</p>
    </div>
  );
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Date(`${value}T00:00:00`).toLocaleDateString();
}
