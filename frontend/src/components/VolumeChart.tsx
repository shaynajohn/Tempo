"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { kmToMiles } from "@/lib/api";

export function VolumeChart({
  data,
}: {
  data: { week: string; km: number }[];
}) {
  if (!data.length) {
    return (
      <p className="py-8 text-center text-sm text-tempo-muted">No volume data yet.</p>
    );
  }

  const chartData = data.map((d) => ({
    ...d,
    miles: Number(kmToMiles(d.km).toFixed(1)),
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e2a36" />
        <XAxis dataKey="week" stroke="#8b9aab" fontSize={10} angle={-20} textAnchor="end" height={50} />
        <YAxis stroke="#8b9aab" fontSize={11} unit=" mi" />
        <Tooltip
          contentStyle={{ background: "#121a22", border: "1px solid #1e2a36", borderRadius: 8 }}
          formatter={(v: number) => [`${v} mi`, "Volume"]}
        />
        <Bar dataKey="miles" fill="#3dd6c6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
