"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function WellnessChart({
  data,
}: {
  data: {
    date: string;
    resting_hr?: number | null;
    sleep_hours?: number | null;
    hrv?: number | null;
  }[];
}) {
  if (!data.length) {
    return (
      <p className="py-8 text-center text-sm text-tempo-muted">
        Import daily wellness data to see sleep & HR trends.
      </p>
    );
  }

  const chartData = data.map((d) => ({
    label: d.date.slice(5),
    resting_hr: d.resting_hr,
    sleep_hours: d.sleep_hours,
    hrv: d.hrv,
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e2a36" />
        <XAxis dataKey="label" stroke="#8b9aab" fontSize={11} />
        <YAxis yAxisId="left" stroke="#f5a623" fontSize={11} />
        <YAxis yAxisId="right" orientation="right" stroke="#3dd6c6" fontSize={11} />
        <Tooltip contentStyle={{ background: "#121a22", border: "1px solid #1e2a36", borderRadius: 8 }} />
        <Legend />
        <Line yAxisId="left" type="monotone" dataKey="resting_hr" stroke="#f5a623" name="Resting HR" dot={false} />
        <Line yAxisId="right" type="monotone" dataKey="sleep_hours" stroke="#3dd6c6" name="Sleep (h)" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
