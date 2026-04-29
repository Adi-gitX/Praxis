"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function ReturnHistogram({ returns, height = 180 }: { returns: number[]; height?: number }) {
  const bins = 24;
  const max = Math.max(...returns.map(Math.abs));
  const lo = -max;
  const hi = max;
  const step = (hi - lo) / bins;
  const counts = new Array(bins).fill(0).map((_, i) => ({
    bucket: (lo + step * (i + 0.5)) * 100,
    count: 0,
    pos: 0,
    neg: 0,
  }));
  for (const r of returns) {
    const idx = Math.min(bins - 1, Math.max(0, Math.floor((r - lo) / step)));
    counts[idx].count += 1;
    if (r >= 0) counts[idx].pos += 1;
    else counts[idx].neg += 1;
  }
  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <BarChart data={counts} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <XAxis
            dataKey="bucket"
            tickFormatter={(v: number) => `${v.toFixed(1)}%`}
            tick={{ fontSize: 10, fontFamily: "var(--font-geist-mono)", fill: "var(--text-tertiary)" }}
            tickLine={false}
            axisLine={false}
            minTickGap={40}
          />
          <YAxis
            tick={{ fontSize: 10, fontFamily: "var(--font-geist-mono)", fill: "var(--text-tertiary)" }}
            tickLine={false}
            axisLine={false}
            width={32}
          />
          <Tooltip
            contentStyle={{
              background: "var(--bg-overlay)",
              border: "1px solid var(--border-default)",
              fontFamily: "var(--font-geist-mono)",
              fontSize: 12,
            }}
            cursor={{ fill: "var(--bg-inset)" }}
            labelFormatter={(v: number) => `bucket: ${Number(v).toFixed(2)}%`}
          />
          <Bar dataKey="neg" stackId="r" fill="var(--neg)" />
          <Bar dataKey="pos" stackId="r" fill="var(--pos)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
