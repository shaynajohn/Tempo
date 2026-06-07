import { formatKmAsMiles, type ReadinessData } from "@/lib/api";
import { cn } from "@/lib/utils";

const ringColor: Record<ReadinessData["level"], string> = {
  high: "border-tempo-accent text-tempo-accent",
  moderate: "border-tempo-warn text-tempo-warn",
  low: "border-tempo-danger text-tempo-danger",
  unknown: "border-tempo-border text-tempo-muted",
};

export function ReadinessCard({
  readiness,
  isHistorical = false,
}: {
  readiness: ReadinessData;
  isHistorical?: boolean;
}) {
  const topFactors = readiness.factors.slice(0, 4);
  const scoreGradient = `conic-gradient(from 180deg, rgba(61,214,198,0.95) ${readiness.score * 3.6}deg, rgba(255,255,255,0.08) 0deg)`;

  return (
    <section className="premium-card p-6">
      <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="eyebrow">
            {isHistorical ? "Latest Readiness Snapshot" : "Today Readiness"}
          </p>
          <h2 className="mt-3 max-w-2xl text-2xl font-semibold leading-tight tracking-tight">
            {readiness.recommendation}
          </h2>
          {readiness.latest_metric_date && (
            <p className="mt-2 text-xs text-tempo-muted">
              Based on latest wellness data from{" "}
              {new Date(readiness.latest_metric_date).toLocaleDateString()}
            </p>
          )}
        </div>

        <div
          className={cn(
            "soft-pulse flex h-32 w-32 shrink-0 items-center justify-center rounded-full p-1",
            ringColor[readiness.level]
          )}
          style={{ background: scoreGradient }}
        >
          <div className="flex h-full w-full items-center justify-center rounded-full bg-tempo-bg text-center shadow-inner shadow-black/60">
            <div>
              <p className="text-4xl font-semibold tabular-nums">{readiness.score}</p>
              <p className="text-xs uppercase tracking-[0.2em]">{readiness.level}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MiniMetric
          label="Sleep"
          value={
            readiness.metrics.sleep_hours
              ? `${readiness.metrics.sleep_hours.toFixed(1)}h`
              : "—"
          }
        />
        <MiniMetric
          label="Resting HR"
          value={
            readiness.metrics.resting_hr
              ? `${Math.round(readiness.metrics.resting_hr)} bpm`
              : "—"
          }
        />
        <MiniMetric
          label="Stress"
          value={
            readiness.metrics.stress_avg
              ? String(Math.round(readiness.metrics.stress_avg))
              : "—"
          }
        />
        <MiniMetric
          label="7-day volume"
          value={
            readiness.training.last_7_days_km != null
              ? formatKmAsMiles(readiness.training.last_7_days_km)
              : "—"
          }
        />
      </div>

      {topFactors.length > 0 && (
        <div className="mt-5 flex flex-wrap gap-2">
          {topFactors.map((factor) => (
            <span
              key={`${factor.label}-${factor.detail}`}
              className={cn(
                "rounded-full px-3 py-1 text-xs",
                factor.impact === "positive" &&
                  "bg-tempo-accent/10 text-tempo-accent",
                factor.impact === "negative" &&
                  "bg-tempo-danger/10 text-tempo-danger",
                factor.impact === "neutral" && "bg-white/5 text-tempo-muted"
              )}
            >
              {factor.label}: {factor.detail}
            </span>
          ))}
        </div>
      )}
    </section>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
      <p className="text-xs text-tempo-muted">{label}</p>
      <p className="mt-0.5 font-medium tabular-nums">{value}</p>
    </div>
  );
}
