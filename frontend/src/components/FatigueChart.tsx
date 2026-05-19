"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { FatiguePoint } from "@/lib/api";

export function FatigueChart({ data }: { data: FatiguePoint[] }) {
  if (!data.length) {
    return (
      <p className="py-12 text-center text-sm text-tempo-muted">
        Import wellness data to see fatigue trends.
      </p>
    );
  }

  const chartData = data.map((d) => ({
    date: d.date.slice(5),
    score: d.score,
    risk: d.risk_level,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id="fatigueGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3dd6c6" stopOpacity={0.4} />
            <stop offset="100%" stopColor="#3dd6c6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e2a36" />
        <XAxis dataKey="date" stroke="#8b9aab" fontSize={11} />
        <YAxis domain={[0, 100]} stroke="#8b9aab" fontSize={11} />
        <Tooltip
          contentStyle={{
            background: "#121a22",
            border: "1px solid #1e2a36",
            borderRadius: 8,
          }}
        />
        <Area
          type="monotone"
          dataKey="score"
          stroke="#3dd6c6"
          fill="url(#fatigueGrad)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
