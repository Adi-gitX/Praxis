import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "praxis · per-strategy tearsheet";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const STRATEGIES: Record<string, { sharpe: string; dsr: string; maxDD: string; universe: string }> = {
  trend_following: { sharpe: "1.28", dsr: "0.41", maxDD: "12.4%", universe: "BTC · ETH · SOL · ARB" },
  stat_arb: { sharpe: "0.46", dsr: "0.12", maxDD: "8.1%", universe: "BTC × ETH" },
  vol_target: { sharpe: "0.71", dsr: "0.18", maxDD: "11.7%", universe: "BTC · ETH · SOL · AVAX" },
};

export default async function OG({ params }: { params: { id: string } }) {
  const m = STRATEGIES[params.id] ?? { sharpe: "—", dsr: "—", maxDD: "—", universe: "—" };

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "#08090A",
          color: "#E6E8EB",
          display: "flex",
          flexDirection: "column",
          fontFamily: "monospace",
          padding: 64,
          position: "relative",
        }}
      >
        <div style={{ position: "absolute", top: 0, left: 0, width: 8, height: "100%", background: "#6E7BFF" }} />

        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <svg width={48} height={48} viewBox="0 0 24 24">
            <polygon points="12,2 22,20 2,20" fill="#6E7BFF" />
          </svg>
          <span style={{ fontSize: 36, color: "#9BA1A8" }}>praxis · strategy</span>
        </div>

        <div style={{ marginTop: 24, fontSize: 84, fontWeight: 600, letterSpacing: -2 }}>{params.id}</div>
        <div style={{ marginTop: 8, fontSize: 24, color: "#6B7280" }}>{m.universe}</div>

        <div style={{ marginTop: "auto", display: "flex", gap: 64 }}>
          <Stat label="SHARPE" value={m.sharpe} color="#00C896" />
          <Stat label="DSR (N=6)" value={m.dsr} color="#E6E8EB" />
          <Stat label="MAX DD" value={m.maxDD} color="#FF5C5C" />
        </div>

        <div style={{ marginTop: 32, color: "#6B7280", fontSize: 20 }}>theory becomes execution</div>
      </div>
    ),
    { ...size },
  );
}

function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <span style={{ fontSize: 16, color: "#6B7280", textTransform: "uppercase", letterSpacing: 2 }}>{label}</span>
      <span style={{ fontSize: 64, fontWeight: 600, color }}>{value}</span>
    </div>
  );
}
