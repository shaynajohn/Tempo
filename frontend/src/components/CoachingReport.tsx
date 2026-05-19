"use client";

import { useEffect, useState } from "react";
import { getCoachingReport, type CoachingReportData } from "@/lib/api";

export function CoachingReport() {
  const [report, setReport] = useState<CoachingReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCoachingReport()
      .then(setReport)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-sm text-tempo-muted">Generating coaching report…</p>;
  }

  if (error) {
    return <p className="text-sm text-tempo-danger">{error}</p>;
  }

  if (!report) return null;

  return (
    <div className="space-y-4">
      {report.final_report && (
        <p className="text-sm leading-relaxed">{report.final_report}</p>
      )}
      {report.forecast && (
        <p className="rounded-lg bg-tempo-accent/5 px-3 py-2 text-sm text-tempo-accent">
          {report.forecast}
        </p>
      )}
      {report.patterns && report.patterns.length > 0 && (
        <ul className="space-y-2 border-t border-tempo-border pt-4">
          {report.patterns.map((p, i) => (
            <li key={i} className="text-xs text-tempo-muted">
              <span className="text-white">{p.title}:</span> {p.description}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
