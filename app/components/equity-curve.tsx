"use client";

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { EquityPoint } from "@/lib/demo-data";

export function EquityCurve({
  data,
  showBenchmark = true,
  height = 220,
  showDrawdown = true,
}: {
  data: EquityPoint[];
  showBenchmark?: boolean;
  height?: number;
  showDrawdown?: boolean;
}) {
  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="equityFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.18} />
              <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="ddFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--neg)" stopOpacity={0} />
              <stop offset="100%" stopColor="var(--neg)" stopOpacity={0.16} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--border-subtle)" vertical={false} />
          <XAxis
            dataKey="ts"
            stroke="var(--text-tertiary)"
            tick={{ fontSize: 11, fontFamily: "var(--font-geist-mono)", fill: "var(--text-tertiary)" }}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
            minTickGap={48}
          />
          <YAxis
            yAxisId="equity"
            stroke="var(--text-tertiary)"
            tick={{ fontSize: 11, fontFamily: "var(--font-geist-mono)", fill: "var(--text-tertiary)" }}
            tickLine={false}
            axisLine={false}
            domain={["auto", "auto"]}
            width={64}
            tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
          />
          {showDrawdown ? (
            <YAxis
              yAxisId="dd"
              orientation="right"
              stroke="var(--text-tertiary)"
              tick={{ fontSize: 11, fontFamily: "var(--font-geist-mono)", fill: "var(--text-tertiary)" }}
              tickLine={false}
              axisLine={false}
              width={48}
              domain={[-0.4, 0]}
              tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
            />
          ) : null}
          <Tooltip
            contentStyle={{
              background: "var(--bg-overlay)",
              border: "1px solid var(--border-default)",
              fontFamily: "var(--font-geist-mono)",
              fontSize: 12,
              color: "var(--text-primary)",
              padding: "8px 12px",
            }}
            cursor={{ stroke: "var(--border-strong)" }}
            formatter={(value: number, key) => {
              if (key === "drawdown") return [`${(value * 100).toFixed(2)}%`, "drawdown"];
              return [`$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, key as string];
            }}
            labelStyle={{ color: "var(--text-tertiary)" }}
          />
          {showBenchmark ? (
            <Line
              yAxisId="equity"
              type="monotone"
              dataKey="benchmark"
              stroke="var(--text-tertiary)"
              strokeWidth={1}
              strokeDasharray="3 3"
              dot={false}
              isAnimationActive={false}
            />
          ) : null}
          {showDrawdown ? (
            <Area
              yAxisId="dd"
              type="monotone"
              dataKey="drawdown"
              stroke="var(--neg)"
              strokeWidth={1}
              fill="url(#ddFill)"
              isAnimationActive={false}
            />
          ) : null}
          <Area
            yAxisId="equity"
            type="monotone"
            dataKey="equity"
            stroke="var(--accent)"
            strokeWidth={1.5}
            fill="url(#equityFill)"
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
