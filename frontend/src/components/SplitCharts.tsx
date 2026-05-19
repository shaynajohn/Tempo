"use client";

import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface Split {
  distance_m?: number;
  duration_s?: number;
  avg_hr?: number;
  avg_cadence?: number;
  avg_pace_s_per_km?: number;
}

function paceToMinKm(secPerKm: number): number {
  return secPerKm / 60;
}

export function SplitCharts({ splits }: { splits: Split[] }) {
  const data = splits
    .map((s, i) => ({
      split: i + 1,
      pace: s.avg_pace_s_per_km ? paceToMinKm(s.avg_pace_s_per_km) : null,
      hr: s.avg_hr ?? null,
      cadence: s.avg_cadence ?? null,
    }))
    .filter((d) => d.pace != null || d.hr != null);

  if (!data.length) {
    return (
      <p className="py-8 text-center text-sm text-tempo-muted">
        No split data for this activity.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="mb-3 text-sm font-medium text-tempo-muted">Pace by split (min/km)</h3>
        <ResponsiveContainer width="100%" height={200}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2a36" />
            <XAxis dataKey="split" stroke="#8b9aab" fontSize={11} label={{ value: "Split", position: "insideBottom", offset: -2 }} />
            <YAxis stroke="#8b9aab" fontSize={11} domain={["auto", "auto"]} />
            <Tooltip
              contentStyle={{ background: "#121a22", border: "1px solid #1e2a36", borderRadius: 8 }}
              formatter={(v: number) => [`${v.toFixed(2)} min/km`, "Pace"]}
            />
            <Bar dataKey="pace" fill="#3dd6c6" radius={[4, 4, 0, 0]} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {(data.some((d) => d.hr) || data.some((d) => d.cadence)) && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-tempo-muted">HR & cadence</h3>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2a36" />
              <XAxis dataKey="split" stroke="#8b9aab" fontSize={11} />
              <YAxis yAxisId="hr" stroke="#f5a623" fontSize={11} />
              <YAxis yAxisId="cadence" orientation="right" stroke="#8b9aab" fontSize={11} />
              <Tooltip contentStyle={{ background: "#121a22", border: "1px solid #1e2a36", borderRadius: 8 }} />
              <Legend />
              {data.some((d) => d.hr) && (
                <Line yAxisId="hr" type="monotone" dataKey="hr" stroke="#f5a623" strokeWidth={2} name="HR (bpm)" dot />
              )}
              {data.some((d) => d.cadence) && (
                <Line yAxisId="cadence" type="monotone" dataKey="cadence" stroke="#8b9aab" strokeWidth={2} name="Cadence" dot />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
