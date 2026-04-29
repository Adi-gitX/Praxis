import { cn } from "@/lib/utils";

type Status = "live" | "paper" | "backtest" | "stopped" | "halted";

const STYLE: Record<Status, string> = {
  live: "border-pos text-pos bg-pos-muted",
  paper: "border-info text-info bg-bg-overlay",
  backtest: "border-accent text-accent bg-accent-muted",
  stopped: "border-border-strong text-text-tertiary bg-bg-overlay",
  halted: "border-neg text-neg bg-neg-muted",
};

const LABEL: Record<Status, string> = {
  live: "LIVE",
  paper: "PAPER",
  backtest: "BACKTEST",
  stopped: "STOPPED",
  halted: "HALTED",
};

export function StatusPill({ status, className }: { status: Status; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 mono text-2xs uppercase tracking-meta border",
        STYLE[status],
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current animate-pulse" />
      {LABEL[status]}
    </span>
  );
}
