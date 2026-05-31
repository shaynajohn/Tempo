"use client";

import { useEffect, useState } from "react";
import {
  getDashboard,
  getFatigue,
  getPatterns,
  getInsights,
  getTrends,
  getReadiness,
  formatKmAsMiles,
  type DashboardStats,
  type FatigueData,
  type Pattern,
  type Insight,
  type TrendsData,
  type ReadinessData,
} from "@/lib/api";
import { StatCard } from "./StatCard";
import { FatigueChart } from "./FatigueChart";
import { PatternCard } from "./PatternCard";
import { CoachingReport } from "./CoachingReport";
import { VolumeChart } from "./VolumeChart";
import { PaceTrendChart, PaceTrendLinks } from "./PaceTrendChart";
import { ReadinessCard } from "./ReadinessCard";
import { WellnessChart } from "./WellnessChart";
import { riskColor } from "@/lib/utils";

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [fatigue, setFatigue] = useState<FatigueData | null>(null);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [trends, setTrends] = useState<TrendsData | null>(null);
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getDashboard(),
      getFatigue(),
      getPatterns(),
      getInsights(),
      getTrends(),
      getReadiness(),
    ])
      .then(([s, f, p, i, t, r]) => {
        setStats(s);
        setFatigue(f);
        setPatterns(p.filter((x) => x.pattern_type !== "insufficient_data"));
        setInsights(i.slice(0, 3));
        setTrends(t);
        setReadiness(r);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="rounded-xl border border-tempo-danger/30 bg-tempo-danger/10 p-6 text-sm">
        <p className="font-medium text-tempo-danger">Cannot reach API</p>
        <p className="mt-2 text-tempo-muted">
          Start the backend (required):{" "}
          <code className="text-white">
            cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8001
          </code>
        </p>
        <p className="mt-1 text-xs text-tempo-muted">
          Then restart the frontend (Ctrl+C, npm run dev). Check:{" "}
          <a href="http://localhost:8001/health" className="text-tempo-accent underline" target="_blank" rel="noreferrer">
            localhost:8001/health
          </a>
        </p>
        <p className="mt-1 text-xs text-tempo-muted">{error}</p>
      </div>
    );
  }

  if (!stats) {
    return <p className="text-tempo-muted">Loading…</p>;
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-tempo-muted">
          Recovery, patterns, and coaching insights from your Garmin data.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Activities" value={String(stats.total_activities)} />
        <StatCard
          label="Total distance"
          value={formatKmAsMiles(stats.total_distance_km)}
        />
        <StatCard
          label="Fatigue score"
          value={fatigue ? String(Math.round(fatigue.current_score)) : "—"}
          sub={fatigue ? fatigue.risk_level : undefined}
        />
        <StatCard label="Insights" value={String(stats.recent_insights)} />
      </div>

      {readiness && <ReadinessCard readiness={readiness} />}

      {stats.total_activities > 0 && (
        <section className="rounded-xl border border-tempo-border bg-tempo-surface p-6">
          <h2 className="text-lg font-medium">Coaching report</h2>
          <p className="mt-1 text-xs text-tempo-muted">
            AI synthesis of fatigue, patterns, and training load
          </p>
          <div className="mt-4">
            <CoachingReport />
          </div>
        </section>
      )}

      {trends && stats.total_activities > 0 && (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-xl border border-tempo-border bg-tempo-surface p-6">
            <h2 className="mb-4 text-lg font-medium">Weekly volume</h2>
            <VolumeChart data={trends.weekly_volume} />
          </section>
          <section className="rounded-xl border border-tempo-border bg-tempo-surface p-6">
            <h2 className="mb-4 text-lg font-medium">Pace trend</h2>
            <PaceTrendChart data={trends.pace_trend} />
            <PaceTrendLinks data={trends.pace_trend} />
          </section>
        </div>
      )}

      {trends && trends.wellness.length > 0 && (
        <section className="rounded-xl border border-tempo-border bg-tempo-surface p-6">
          <h2 className="mb-4 text-lg font-medium">Sleep & resting HR</h2>
          <WellnessChart data={trends.wellness} />
        </section>
      )}

      {fatigue && (
        <section className="rounded-xl border border-tempo-border bg-tempo-surface p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-medium">Fatigue & burnout risk</h2>
            <span
              className={`text-sm font-medium capitalize ${riskColor(fatigue.risk_level)}`}
            >
              {fatigue.risk_level}
            </span>
          </div>
          <FatigueChart data={fatigue.trend} />
          <p className="mt-4 text-sm text-tempo-muted">{fatigue.recommendation}</p>
        </section>
      )}

      {patterns.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-medium">Training patterns</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {patterns.map((p) => (
              <PatternCard key={p.pattern_type + p.title} pattern={p} />
            ))}
          </div>
        </section>
      )}

      {insights.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-medium">Recent insights</h2>
          <div className="space-y-3">
            {insights.map((i) => (
              <article
                key={i.id}
                className="rounded-xl border border-tempo-border bg-tempo-surface p-5"
              >
                <h3 className="font-medium">{i.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-tempo-muted">
                  {i.body}
                </p>
              </article>
            ))}
          </div>
        </section>
      )}

      {stats.total_activities === 0 && (
        <div className="rounded-xl border border-dashed border-tempo-border p-8 text-center">
          <p className="text-tempo-muted">No data yet.</p>
          <a
            href="/import"
            className="mt-2 inline-block text-tempo-accent hover:underline"
          >
            Import sample data while you wait for Garmin →
          </a>
        </div>
      )}
    </div>
  );
}
