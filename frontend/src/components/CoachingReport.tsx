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
    return (
      <div className="space-y-3">
        <div className="h-3 w-2/3 rounded-full bg-white/10" />
        <div className="h-3 w-5/6 rounded-full bg-white/10" />
        <p className="text-sm text-tempo-muted">Generating coaching report...</p>
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-tempo-danger">{error}</p>;
  }

  if (!report) return null;

  return (
    <div className="space-y-4">
      {report.final_report && (
        <p className="text-base leading-7 text-white/90">{report.final_report}</p>
      )}
      {report.forecast && (
        <p className="rounded-xl border border-tempo-accent/20 bg-tempo-accent/10 px-4 py-3 text-sm text-tempo-accent">
          {report.forecast}
        </p>
      )}
      {report.patterns && report.patterns.length > 0 && (
        <ul className="space-y-2 border-t border-white/10 pt-4">
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
