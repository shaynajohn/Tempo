"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  explainRun,
  formatDistance,
  formatPace,
  getActivity,
  type Activity,
  type Insight,
} from "@/lib/api";
import { SplitCharts } from "@/components/SplitCharts";

export default function ActivityDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const [activity, setActivity] = useState<Activity | null>(null);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(true);
  const [explaining, setExplaining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id || Number.isNaN(id)) return;
    getActivity(id)
      .then(setActivity)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleExplain() {
    setExplaining(true);
    try {
      const result = await explainRun(id);
      setInsight(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Explain failed");
    } finally {
      setExplaining(false);
    }
  }

  if (loading) return <p className="text-tempo-muted">Loading…</p>;
  if (error && !activity) {
    return (
      <p className="text-tempo-danger">
        {error}. <Link href="/activities" className="text-tempo-accent">Back</Link>
      </p>
    );
  }
  if (!activity) return null;

  const durationMin = activity.duration_s
    ? Math.round(activity.duration_s / 60)
    : null;

  return (
    <div className="space-y-8">
      <div>
        <Link href="/activities" className="text-sm text-tempo-muted hover:text-white">
          ← Activities
        </Link>
        <h1 className="mt-2 text-3xl font-semibold">{activity.name || "Run"}</h1>
        <p className="mt-1 text-tempo-muted">
          {new Date(activity.started_at).toLocaleString(undefined, {
            weekday: "long",
            month: "long",
            day: "numeric",
            year: "numeric",
            hour: "numeric",
            minute: "2-digit",
          })}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Distance" value={formatDistance(activity.distance_m)} />
        <Metric label="Pace" value={formatPace(activity.avg_pace_s_per_km)} />
        <Metric label="Avg HR" value={activity.avg_hr ? `${Math.round(activity.avg_hr)} bpm` : "—"} />
        <Metric label="Duration" value={durationMin ? `${durationMin} min` : "—"} />
        {activity.avg_cadence != null && (
          <Metric label="Cadence" value={`${Math.round(activity.avg_cadence)} spm`} />
        )}
        {activity.temperature_c != null && (
          <Metric label="Temp" value={`${Math.round(activity.temperature_c)}°C`} />
        )}
        {activity.training_load != null && (
          <Metric label="Training load" value={activity.training_load.toFixed(1)} />
        )}
        {activity.elevation_gain_m != null && (
          <Metric label="Elevation" value={`${Math.round(activity.elevation_gain_m)} m`} />
        )}
      </div>

      {activity.splits && activity.splits.length > 0 && (
        <section className="rounded-xl border border-tempo-border bg-tempo-surface p-6">
          <h2 className="mb-4 text-lg font-medium">Splits & HR drift</h2>
          <SplitCharts splits={activity.splits} />
        </section>
      )}

      <section className="rounded-xl border border-tempo-border bg-tempo-surface p-6">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-lg font-medium">AI explanation</h2>
          <button
            onClick={handleExplain}
            disabled={explaining}
            className="rounded-lg bg-tempo-accent px-4 py-2 text-sm font-medium text-tempo-bg hover:opacity-90 disabled:opacity-50"
          >
            {explaining ? "Analyzing…" : insight ? "Regenerate" : "Explain this run"}
          </button>
        </div>
        {insight ? (
          <p className="mt-4 text-sm leading-relaxed text-tempo-muted">{insight.body}</p>
        ) : (
          <p className="mt-4 text-sm text-tempo-muted">
            Get a coach-style breakdown of pacing, cadence, and fatigue signals.
          </p>
        )}
      </section>

      {activity.summary_text && (
        <p className="text-xs text-tempo-muted">{activity.summary_text}</p>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-tempo-border bg-tempo-surface px-4 py-3">
      <p className="text-xs text-tempo-muted">{label}</p>
      <p className="mt-0.5 font-medium tabular-nums">{value}</p>
    </div>
  );
}
