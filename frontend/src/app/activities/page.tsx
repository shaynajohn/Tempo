"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  getActivities,
  formatPace,
  formatDistance,
  type Activity,
} from "@/lib/api";

export default function ActivitiesPage() {
  const [activities, setActivities] = useState<Activity[]>([]);

  useEffect(() => {
    getActivities().then((r) => setActivities(r.items));
  }, []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold">Activities</h1>
        <p className="mt-1 text-tempo-muted">
          Click a run for splits, charts, and AI explanation.
        </p>
      </header>

      <div className="overflow-hidden rounded-xl border border-tempo-border">
        <table className="w-full text-sm">
          <thead className="bg-tempo-surface text-left text-tempo-muted">
            <tr>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Distance</th>
              <th className="px-4 py-3">Pace</th>
              <th className="px-4 py-3">HR</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {activities.map((a) => (
              <tr key={a.id} className="border-t border-tempo-border hover:bg-tempo-surface/50">
                <td className="px-4 py-3 tabular-nums">
                  {new Date(a.started_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  <Link
                    href={`/activities/${a.id}`}
                    className="font-medium hover:text-tempo-accent"
                  >
                    {a.name || "Run"}
                  </Link>
                </td>
                <td className="px-4 py-3">{formatDistance(a.distance_m)}</td>
                <td className="px-4 py-3">{formatPace(a.avg_pace_s_per_km)}</td>
                <td className="px-4 py-3">
                  {a.avg_hr ? `${Math.round(a.avg_hr)} bpm` : "—"}
                </td>
                <td className="px-4 py-3">
                  <Link
                    href={`/activities/${a.id}`}
                    className="text-xs text-tempo-accent hover:underline"
                  >
                    View →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {activities.length === 0 && (
          <p className="p-8 text-center text-tempo-muted">
            No activities yet.{" "}
            <Link href="/import" className="text-tempo-accent hover:underline">
              Import data
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}
