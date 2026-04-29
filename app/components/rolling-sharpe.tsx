"use client";

import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function RollingSharpe({
  data,
  height = 180,
}: {
  data: { ts: string; sharpe: number }[];
  height?: number;
}) {
  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <XAxis
            dataKey="ts"
            tick={{ fontSize: 10, fontFamily: "var(--font-geist-mono)", fill: "var(--text-tertiary)" }}
            tickLine={false}
            axisLine={false}
            minTickGap={48}
          />
          <YAxis
            tick={{ fontSize: 10, fontFamily: "var(--font-geist-mono)", fill: "var(--text-tertiary)" }}
            tickLine={false}
            axisLine={false}
            width={32}
            domain={["auto", "auto"]}
          />
          <ReferenceLine y={1} stroke="var(--border-default)" strokeDasharray="2 4" />
          <ReferenceLine y={0} stroke="var(--border-strong)" />
          <Tooltip
            contentStyle={{
              background: "var(--bg-overlay)",
              border: "1px solid var(--border-default)",
              fontFamily: "var(--font-geist-mono)",
              fontSize: 12,
            }}
            cursor={{ stroke: "var(--border-strong)" }}
            formatter={(v: number) => [v.toFixed(4), "sharpe"]}
          />
          <Line
            type="monotone"
            dataKey="sharpe"
            stroke="var(--accent)"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
