"use client";

import { useEffect, useState } from "react";
import {
  getDashboard,
  getFatigue,
  getPatterns,
  getInsights,
  getTrends,
  getReadiness,
  getLibraryStatus,
  getActivities,
  formatKmAsMiles,
  type DashboardStats,
  type FatigueData,
  type Pattern,
  type Insight,
  type TrendsData,
  type ReadinessData,
  type LibraryStatus,
  type Activity,
} from "@/lib/api";
import { FatigueChart } from "./FatigueChart";
import { PatternCard } from "./PatternCard";
import { CoachingReport } from "./CoachingReport";
import { CoachBriefHero } from "./CoachBriefHero";
import { VolumeChart } from "./VolumeChart";
import { PaceTrendChart, PaceTrendLinks } from "./PaceTrendChart";
import { WellnessChart } from "./WellnessChart";
import { riskColor } from "@/lib/utils";

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [fatigue, setFatigue] = useState<FatigueData | null>(null);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [trends, setTrends] = useState<TrendsData | null>(null);
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);
  const [libraryStatus, setLibraryStatus] = useState<LibraryStatus | null>(null);
  const [latestActivity, setLatestActivity] = useState<Activity | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getDashboard(),
      getFatigue(),
      getPatterns(),
      getInsights(),
      getTrends(),
      getReadiness(),
      getLibraryStatus(),
      getActivities(1),
    ])
      .then(([s, f, p, i, t, r, library, latest]) => {
        setStats(s);
        setFatigue(f);
        setPatterns(p.filter((x) => x.pattern_type !== "insufficient_data"));
        setInsights(i.slice(0, 3));
        setTrends(t);
        setReadiness(r);
        setLibraryStatus(library);
        setLatestActivity(latest.items[0] ?? null);
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
    return (
      <div className="premium-card p-8">
        <p className="eyebrow">Loading</p>
        <p className="mt-2 text-tempo-muted">Preparing your training command center...</p>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <CoachBriefHero
        readiness={readiness}
        fatigue={fatigue}
        libraryStatus={libraryStatus}
        latestActivity={latestActivity}
      />

      <SignalStrip
        stats={stats}
        fatigue={fatigue}
        readiness={readiness}
        libraryStatus={libraryStatus}
      />

      {stats.total_activities > 0 && (
        <details className="premium-card group p-5">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-4">
            <div>
              <p className="eyebrow">More Context</p>
              <h2 className="mt-1 text-xl font-semibold tracking-tight">AI coaching notes</h2>
            </div>
            <span className="pill group-open:hidden">Show</span>
            <span className="pill hidden group-open:inline-flex">Hide</span>
          </summary>
          <div className="mt-5 border-t border-white/10 pt-5">
            <CoachingReport />
          </div>
        </details>
      )}

      {trends && stats.total_activities > 0 && (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="premium-card p-6">
            <p className="eyebrow">Load</p>
            <h2 className="mb-4 mt-2 text-xl font-semibold">Weekly volume</h2>
            <VolumeChart data={trends.weekly_volume} />
          </section>
          <section className="premium-card p-6">
            <p className="eyebrow">Speed</p>
            <h2 className="mb-4 mt-2 text-xl font-semibold">Pace trend</h2>
            <PaceTrendChart data={trends.pace_trend} />
            <PaceTrendLinks data={trends.pace_trend} />
          </section>
        </div>
      )}

      {trends && trends.wellness.length > 0 && (
        <section className="premium-card p-6">
          <p className="eyebrow">Recovery Signals</p>
          <h2 className="mb-4 mt-2 text-xl font-semibold">Sleep & resting HR</h2>
          <WellnessChart data={trends.wellness} />
        </section>
      )}

      {fatigue && (
        <section className="premium-card p-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="eyebrow">Risk Model</p>
              <h2 className="mt-2 text-xl font-semibold">Fatigue & burnout risk</h2>
            </div>
            <span
              className={`rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-sm font-medium capitalize ${riskColor(fatigue.risk_level)}`}
            >
              {fatigue.risk_level}
            </span>
          </div>
          <FatigueChart data={fatigue.trend} />
          <p className="mt-4 text-sm text-tempo-muted">{fatigue.recommendation}</p>
        </section>
      )}

      {patterns.length > 0 && (
        <details className="group">
          <summary className="mb-4 flex cursor-pointer list-none items-end justify-between gap-4">
            <div>
              <p className="eyebrow">Discovered Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight">Training patterns</h2>
            </div>
            <span className="pill group-open:hidden">Show</span>
            <span className="pill hidden group-open:inline-flex">Hide</span>
          </summary>
          <div className="grid gap-4 md:grid-cols-2">
            {patterns.map((p) => (
              <PatternCard key={p.pattern_type + p.title} pattern={p} />
            ))}
          </div>
        </details>
      )}

      {insights.length > 0 && (
        <section>
          <div className="mb-4">
            <p className="eyebrow">Memory</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight">Recent insights</h2>
          </div>
          <div className="space-y-3">
            {insights.map((i) => (
              <article
                key={i.id}
                className="premium-card p-5"
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

function SignalStrip({
  stats,
  fatigue,
  readiness,
  libraryStatus,
}: {
  stats: DashboardStats;
  fatigue: FatigueData | null;
  readiness: ReadinessData | null;
  libraryStatus: LibraryStatus | null;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Signal label="Runs" value={String(stats.total_activities)} />
      <Signal label="Miles" value={formatKmAsMiles(stats.total_distance_km)} />
      <Signal
        label="Readiness"
        value={readiness ? `${readiness.score}` : "—"}
        tone={readiness?.level === "low" ? "danger" : readiness?.level === "moderate" ? "warn" : "accent"}
      />
      <Signal
        label="Data"
        value={libraryStatus?.freshness ?? "—"}
        tone={libraryStatus?.needs_import ? "warn" : "accent"}
        sub={fatigue ? `${Math.round(fatigue.current_score)} fatigue` : undefined}
      />
    </div>
  );
}

function Signal({
  label,
  value,
  sub,
  tone = "muted",
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "accent" | "warn" | "danger" | "muted";
}) {
  const toneClass = {
    accent: "text-tempo-accent",
    warn: "text-tempo-warn",
    danger: "text-tempo-danger",
    muted: "text-white",
  }[tone];

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.035] px-4 py-3 backdrop-blur">
      <p className="text-xs uppercase tracking-[0.16em] text-tempo-muted">{label}</p>
      <p className={`mt-1 text-2xl font-semibold capitalize tabular-nums ${toneClass}`}>
        {value}
      </p>
      {sub && <p className="mt-1 text-xs text-tempo-muted">{sub}</p>}
    </div>
  );
}

