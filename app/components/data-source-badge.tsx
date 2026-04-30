import Link from "next/link";

import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

/**
 * Honest indicator of where the numbers on a page come from.
 *
 * - `live`   — fetched from the FastAPI server right now (NEXT_PUBLIC_API_URL set)
 * - `seeded` — deterministic mulberry32 demo data (no backend wired)
 *
 * Pages opt into the live mode by passing the resolved `source` from a
 * server-side fetch attempt. The demo mode is the safe default and keeps
 * renders reproducible for reviewers without a backend to point at.
 */
export function DataSourceBadge({
  source,
  className,
}: {
  source?: "live" | "seeded" | "fallback";
  className?: string;
}) {
  const resolved = source ?? (api.isConfigured() ? "live" : "seeded");
  if (resolved === "live") {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1.5 px-2 py-0.5 mono text-2xs uppercase tracking-meta border",
          "border-pos text-pos bg-pos-muted",
          className,
        )}
      >
        <span className="h-1.5 w-1.5 rounded-full bg-current animate-pulse" />
        live · fastapi
      </span>
    );
  }
  if (resolved === "fallback") {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-2 px-2 py-0.5 mono text-2xs uppercase tracking-meta border",
          "border-warn text-warn bg-bg-overlay",
          className,
        )}
      >
        api · unreachable · using seeded
      </span>
    );
  }
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 px-2 py-0.5 mono text-2xs uppercase tracking-meta border",
        "border-border-default text-text-secondary bg-bg-overlay",
        className,
      )}
    >
      seeded · demo data ·
      <Link href="/runs" className="text-accent hover:text-accent-hover">
        view live runs →
      </Link>
    </span>
  );
}
