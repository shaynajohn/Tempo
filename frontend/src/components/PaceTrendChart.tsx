"use client";

import Link from "next/link";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function PaceTrendChart({
  data,
}: {
  data: { date: string; pace: number; name: string; id: number }[];
}) {
  if (!data.length) {
    return (
      <p className="py-8 text-center text-sm text-tempo-muted">No pace data yet.</p>
    );
  }

  const chartData = data.map((d) => ({
    ...d,
    label: d.date.slice(5),
    paceMin: d.pace / 60,
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e2a36" />
        <XAxis dataKey="label" stroke="#8b9aab" fontSize={11} />
        <YAxis stroke="#8b9aab" fontSize={11} domain={["auto", "auto"]} />
        <Tooltip
          contentStyle={{ background: "#121a22", border: "1px solid #1e2a36", borderRadius: 8 }}
          labelFormatter={(_, payload) => payload?.[0]?.payload?.name ?? ""}
          formatter={(v: number) => {
            const m = Math.floor(v);
            const s = Math.round((v - m) * 60);
            return [`${m}:${s.toString().padStart(2, "0")}/km`, "Pace"];
          }}
        />
        <Line
          type="monotone"
          dataKey="paceMin"
          stroke="#3dd6c6"
          strokeWidth={2}
          dot={{ fill: "#3dd6c6", r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function PaceTrendLinks({
  data,
}: {
  data: { date: string; name: string; id: number }[];
}) {
  const recent = [...data].reverse().slice(0, 3);
  if (!recent.length) return null;
  return (
    <p className="mt-2 text-xs text-tempo-muted">
      Recent:{" "}
      {recent.map((d, i) => (
        <span key={d.id}>
          {i > 0 && " · "}
          <Link href={`/activities/${d.id}`} className="text-tempo-accent hover:underline">
            {d.name}
          </Link>
        </span>
      ))}
    </p>
  );
}
