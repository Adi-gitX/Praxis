"use client";

import { useEffect, useRef, useState } from "react";

import { apiBaseUrl } from "@/lib/api";
import { cn } from "@/lib/utils";

type Decision = {
  ts?: string;
  regime?: string;
  notes?: string;
  target_weights?: Record<string, number>;
  [k: string]: unknown;
};

/**
 * Live tail of `decisions.jsonl` from the FastAPI server's SSE endpoint.
 * Renders the most recent N decisions in reverse-chronological order.
 *
 * Falls back to a static "configure NEXT_PUBLIC_API_URL" notice when the
 * API isn't wired — same honesty pattern as the rest of the app.
 */
export function StreamingDecisions({ runId, max = 50 }: { runId: string; max?: number }) {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [status, setStatus] = useState<"idle" | "open" | "error" | "no-api">("idle");
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const base = apiBaseUrl();
    if (!base) {
      setStatus("no-api");
      return;
    }
    const url = `${base}/runs/${encodeURIComponent(runId)}/decisions/stream`;
    const es = new EventSource(url);
    sourceRef.current = es;
    setStatus("idle");

    es.onopen = () => setStatus("open");
    es.onerror = () => setStatus("error");
    es.onmessage = (ev) => {
      try {
        const parsed = JSON.parse(ev.data) as Decision;
        setDecisions((prev) => [parsed, ...prev].slice(0, max));
      } catch {
        // skip malformed lines
      }
    };

    return () => {
      es.close();
      sourceRef.current = null;
    };
  }, [runId, max]);

  if (status === "no-api") {
    return (
      <div className="text-xs text-text-tertiary p-3">
        Set <code className="mono text-accent">NEXT_PUBLIC_API_URL</code> at build
        time to stream the decision log live. The /runs page documents the setup.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-1.5 flex items-center justify-between border-b border-border-subtle">
        <span className="label">streaming · sse</span>
        <span className={cn("mono text-2xs", statusClass(status))}>{statusLabel(status)}</span>
      </div>
      <ul className="flex-1 overflow-y-auto divide-y divide-border-subtle text-xs">
        {decisions.length === 0 ? (
          <li className="p-3 text-text-tertiary mono">waiting for first event...</li>
        ) : (
          decisions.map((d, i) => (
            <li key={i} className="px-3 py-2 flex gap-3 items-baseline">
              <span className="mono text-text-tertiary">{shortTs(d.ts)}</span>
              <span className={cn("mono uppercase tracking-meta", regimeTone(d.regime))}>
                {d.regime ?? "—"}
              </span>
              <span className="text-text-secondary truncate">
                {d.target_weights ? compactDict(d.target_weights) : (d.notes as string) ?? ""}
              </span>
            </li>
          ))
        )}
      </ul>
    </div>
  );
}

function statusClass(s: "idle" | "open" | "error" | "no-api"): string {
  switch (s) {
    case "open":
      return "text-pos";
    case "error":
      return "text-neg";
    case "no-api":
      return "text-text-tertiary";
    default:
      return "text-text-secondary";
  }
}

function statusLabel(s: "idle" | "open" | "error" | "no-api"): string {
  switch (s) {
    case "open":
      return "● connected";
    case "error":
      return "● disconnected";
    case "no-api":
      return "no api";
    default:
      return "connecting…";
  }
}

function shortTs(ts?: string): string {
  if (!ts) return "—";
  const m = /T(\d{2}:\d{2}:\d{2})/.exec(ts);
  return m ? m[1] : ts.slice(0, 19);
}

function regimeTone(r?: string): string {
  switch (r) {
    case "trending":
      return "text-pos";
    case "high_vol":
      return "text-warn";
    case "crisis":
      return "text-neg";
    default:
      return "text-text-secondary";
  }
}

function compactDict(d: Record<string, number>): string {
  return Object.entries(d)
    .slice(0, 4)
    .map(([k, v]) => `${k}=${v.toFixed(3)}`)
    .join(" · ");
}
