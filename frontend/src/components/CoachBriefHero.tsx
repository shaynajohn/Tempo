import Link from "next/link";
import {
  formatDistance,
  formatPace,
  type Activity,
  type FatigueData,
  type LibraryStatus,
  type ReadinessData,
} from "@/lib/api";
import { cn } from "@/lib/utils";

export function CoachBriefHero({
  readiness,
  fatigue,
  libraryStatus,
  latestActivity,
}: {
  readiness: ReadinessData | null;
  fatigue: FatigueData | null;
  libraryStatus: LibraryStatus | null;
  latestActivity: Activity | null;
}) {
  const mode = getMode(libraryStatus);
  const recommendation = getRecommendation(readiness, fatigue, libraryStatus);
  const confidence = getConfidence(libraryStatus, readiness);
  const reasons = getReasons(readiness, fatigue, libraryStatus);

  return (
    <header className="premium-card p-6 sm:p-8">
      <div className="grid gap-6 xl:grid-cols-[1.5fr_0.72fr]">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="eyebrow">Coach Brief</p>
            <span className={cn("pill capitalize", mode.className)}>{mode.label}</span>
            <span className="pill">{confidence} confidence</span>
          </div>

          <h1 className="mt-5 max-w-3xl text-3xl font-semibold leading-[1.02] tracking-[-0.04em] sm:text-5xl">
            {recommendation.title}
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-tempo-muted sm:text-base">
            {recommendation.body}
          </p>

          <div className="mt-6 flex flex-wrap gap-2">
            {reasons.map((reason) => (
              <div
                key={reason.label}
                className="rounded-full border border-white/10 bg-black/20 px-3 py-2"
              >
                <span className="text-xs text-tempo-muted">{reason.label}: </span>
                <span className="text-xs font-medium text-white/90">{reason.detail}</span>
              </div>
            ))}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            {libraryStatus?.needs_import ? (
              <Link
                href="/import"
                className="rounded-xl bg-tempo-accent px-5 py-3 text-sm font-semibold text-tempo-bg shadow-lg shadow-tempo-accent/20 transition hover:opacity-90"
              >
                Import fresh Garmin data
              </Link>
            ) : (
              <Link
                href="/activities"
                className="rounded-xl bg-tempo-accent px-5 py-3 text-sm font-semibold text-tempo-bg shadow-lg shadow-tempo-accent/20 transition hover:opacity-90"
              >
                Review activities
              </Link>
            )}
            <Link
              href="/performance"
              className="rounded-xl border border-white/10 bg-white/[0.06] px-5 py-3 text-sm font-medium text-white transition hover:bg-white/[0.1]"
            >
              View projections
            </Link>
          </div>
        </div>

        <aside className="rounded-3xl border border-white/10 bg-black/25 p-5">
          <p className="eyebrow">Latest Run</p>
          {latestActivity ? (
            <Link href={`/activities/${latestActivity.id}`} className="group block">
              <h2 className="mt-3 text-xl font-semibold group-hover:text-tempo-accent">
                {latestActivity.name || "Run"}
              </h2>
              <p className="mt-1 text-sm text-tempo-muted">
                {new Date(latestActivity.started_at).toLocaleDateString()}
              </p>
              <p className="mt-4 text-sm text-white/90">
                {formatDistance(latestActivity.distance_m)} ·{" "}
                {formatPace(latestActivity.avg_pace_s_per_km)}
                {latestActivity.avg_hr
                  ? ` · ${Math.round(latestActivity.avg_hr)} bpm`
                  : ""}
              </p>
            </Link>
          ) : (
            <p className="mt-3 text-sm text-tempo-muted">
              Import Garmin data to anchor recommendations to your latest workout.
            </p>
          )}
        </aside>
      </div>
    </header>
  );
}

function getMode(status: LibraryStatus | null) {
  if (!status) return { label: "Loading", className: "text-tempo-muted" };
  if (status.freshness === "fresh") {
    return { label: "Live mode", className: "text-tempo-accent" };
  }
  if (status.freshness === "aging") {
    return { label: "Aging data", className: "text-tempo-warn" };
  }
  if (status.freshness === "stale") {
    return { label: "Historical mode", className: "text-tempo-danger" };
  }
  return { label: "No data", className: "text-tempo-muted" };
}

function getConfidence(
  status: LibraryStatus | null,
  readiness: ReadinessData | null
): "high" | "medium" | "low" {
  if (!status || status.freshness === "empty" || !readiness) return "low";
  if (status.freshness === "fresh" && readiness.factors.length >= 3) return "high";
  if (status.freshness === "stale") return "low";
  return "medium";
}

function getRecommendation(
  readiness: ReadinessData | null,
  fatigue: FatigueData | null,
  status: LibraryStatus | null
) {
  if (!status || status.freshness === "empty") {
    return {
      title: "Import Garmin data to unlock coaching.",
      body: "Tempo needs activities and wellness data before it can assess training readiness.",
    };
  }

  const stalePrefix =
    status.freshness === "stale"
      ? "This is a historical snapshot, not a live recommendation. "
      : "";

  if (status.freshness === "stale") {
    return {
      title: "Historical snapshot. Refresh before planning today.",
      body: status.summary,
    };
  }

  if (readiness?.level === "low" || fatigue?.risk_level === "high") {
    return {
      title: "Keep it easy today.",
      body: `${stalePrefix}${readiness?.recommendation ?? "Recovery signals are elevated."}`,
    };
  }

  if (readiness?.level === "high" && fatigue?.risk_level === "low") {
    return {
      title: "Quality work is on the table.",
      body: `${stalePrefix}${readiness.recommendation}`,
    };
  }

  return {
    title: "Train, but keep it flexible.",
    body: `${stalePrefix}${readiness?.recommendation ?? "Tempo has enough data for a moderate-confidence read."}`,
  };
}

function getReasons(
  readiness: ReadinessData | null,
  fatigue: FatigueData | null,
  status: LibraryStatus | null
) {
  const freshness =
    status?.days_since_latest == null
      ? "No imported data yet."
      : `${status.days_since_latest}d old`;

  const readinessReason = readiness
    ? `${readiness.score}/100`
    : "Readiness unavailable.";

  const fatigueReason = fatigue
    ? `${Math.round(fatigue.current_score)}/100 ${fatigue.risk_level}`
    : "Fatigue unavailable.";

  return [
    { label: "Freshness", detail: freshness },
    { label: "Readiness", detail: readinessReason },
    { label: "Fatigue", detail: fatigueReason },
  ];
}
