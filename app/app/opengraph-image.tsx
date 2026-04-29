import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "praxis · theory becomes execution";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OG() {
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
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: 8,
            height: "100%",
            background: "#6E7BFF",
          }}
        />
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <svg width={88} height={88} viewBox="0 0 24 24">
            <polygon points="12,2 22,20 2,20" fill="#6E7BFF" />
          </svg>
          <span style={{ fontSize: 96, fontWeight: 600, letterSpacing: -2, color: "#E6E8EB" }}>
            praxis
          </span>
        </div>

        <div style={{ marginTop: 48, fontSize: 36, color: "#9BA1A8", lineHeight: 1.3, maxWidth: 980 }}>
          A research framework for autonomous quantitative trading on on-chain markets.
        </div>

        <div
          style={{
            marginTop: "auto",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            color: "#6B7280",
            fontSize: 24,
          }}
        >
          <span>theory becomes execution</span>
          <span>v0.1.0 · MIT</span>
        </div>
      </div>
    ),
    { ...size },
  );
}
