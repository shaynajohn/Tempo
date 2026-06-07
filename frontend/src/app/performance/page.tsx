"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  formatDistance,
  formatPace,
  getPerformance,
  type PerformanceData,
  type PerformanceMark,
} from "@/lib/api";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function PerformancePage() {
  const [data, setData] = useState<PerformanceData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPerformance().then(setData).catch((e) => setError(e.message));
  }, []);

  const chartData = useMemo(
    () =>
      data?.race_projections.map((p) => ({
        distance: p.distance_label,
        minutes: p.seconds / 60,
        time: p.formatted_time,
      })) ?? [],
    [data]
  );

  if (error) {
    return (
      <div className="rounded-xl border border-tempo-danger/30 bg-tempo-danger/10 p-6 text-sm text-tempo-danger">
        {error}
      </div>
    );
  }

  if (!data) {
    return <p className="text-tempo-muted">Loading performance analytics...</p>;
  }

  return (
    <div className="space-y-8">
      <header className="premium-card p-6">
        <p className="eyebrow">Race Engine</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">Performance</h1>
        <p className="mt-2 max-w-2xl text-tempo-muted">
          Personal-best estimates and race projections from your imported runs.
        </p>
      </header>

      <section className="premium-card p-6">
        <p className="eyebrow">Projection Model</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight">Race projections</h2>
        <p className="mt-1 text-sm text-tempo-muted">{data.summary}</p>
        <div className="mt-6">
          <ProjectionChart data={chartData} />
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="premium-card p-6">
          <p className="eyebrow">Targets</p>
          <h2 className="mb-4 mt-2 text-xl font-semibold">Projected race times</h2>
          <div className="space-y-3">
            {data.race_projections.map((projection) => (
              <PerformanceRow key={projection.distance_key} mark={projection} />
            ))}
          </div>
        </section>

        <section className="premium-card p-6">
          <p className="eyebrow">Benchmarks</p>
          <h2 className="mb-4 mt-2 text-xl font-semibold">Estimated personal bests</h2>
          {data.personal_bests.length ? (
            <div className="space-y-3">
              {data.personal_bests.map((pb) => (
                <PerformanceRow key={pb.distance_key} mark={pb} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-tempo-muted">
              Import longer runs to estimate personal bests.
            </p>
          )}
        </section>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {data.fastest_run && (
          <RunCard title="Fastest average pace" activity={data.fastest_run} />
        )}
        {data.longest_run && <RunCard title="Longest run" activity={data.longest_run} />}
        {data.projection_source && (
          <RunCard title="Projection source" activity={data.projection_source} />
        )}
      </div>
    </div>
  );
}

function ProjectionChart({
  data,
}: {
  data: { distance: string; minutes: number; time: string }[];
}) {
  if (!data.length) {
    return (
      <p className="py-8 text-center text-sm text-tempo-muted">
        No projection data yet.
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e2a36" />
        <XAxis dataKey="distance" stroke="#8b9aab" fontSize={11} />
        <YAxis stroke="#8b9aab" fontSize={11} unit=" min" />
        <Tooltip
          contentStyle={{
            background: "#121a22",
            border: "1px solid #1e2a36",
            borderRadius: 8,
          }}
          formatter={(value) => [`${Number(value).toFixed(1)} min`, "Projected time"]}
        />
        <Bar dataKey="minutes" fill="#3dd6c6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function PerformanceRow({ mark }: { mark: PerformanceMark }) {
  const activity = mark.activity ?? mark.source_activity;
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-4 transition hover:border-tempo-accent/30">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-medium">{mark.distance_label}</p>
          <p className="mt-1 text-xs text-tempo-muted">
            {formatPace(mark.pace_s_per_km)} average
          </p>
        </div>
        <p className="text-xl font-semibold tabular-nums text-tempo-accent">
          {mark.formatted_time}
        </p>
      </div>
      {activity && (
        <p className="mt-3 text-xs text-tempo-muted">
          Based on{" "}
          <Link
            href={`/activities/${activity.id}`}
            className="text-tempo-accent hover:underline"
          >
            {activity.name}
          </Link>
          {" · "}
          {new Date(activity.started_at).toLocaleDateString()}
        </p>
      )}
    </div>
  );
}

function RunCard({
  title,
  activity,
}: {
  title: string;
  activity: NonNullable<PerformanceData["fastest_run"]>;
}) {
  return (
    <Link
      href={`/activities/${activity.id}`}
      className="premium-card p-5 transition hover:-translate-y-0.5 hover:border-tempo-accent/60"
    >
      <p className="text-xs uppercase tracking-[0.18em] text-tempo-muted">{title}</p>
      <p className="mt-1 font-medium">{activity.name}</p>
      <p className="mt-2 text-sm text-tempo-muted">
        {formatDistance(activity.distance_m)} · {formatPace(activity.pace_s_per_km)}
      </p>
    </Link>
  );
}
