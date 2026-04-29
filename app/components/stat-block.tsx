import { cn } from "@/lib/utils";

export function StatBlock({
  label,
  value,
  delta,
  deltaLabel,
  tone = "neutral",
  size = "md",
  className,
}: {
  label: string;
  value: string;
  delta?: string;
  deltaLabel?: string;
  tone?: "neutral" | "pos" | "neg" | "warn";
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const toneClasses = {
    neutral: "text-text-primary",
    pos: "text-pos",
    neg: "text-neg",
    warn: "text-warn",
  } as const;
  const valueSize = size === "lg" ? "text-3xl" : size === "sm" ? "text-md" : "text-2xl";
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <span className="label">{label}</span>
      <span className={cn("mono tabular font-semibold", valueSize, toneClasses[tone])}>{value}</span>
      {delta !== undefined && (
        <span className="mono text-xs text-text-secondary tabular">
          <span className={tone === "neg" ? "text-neg" : tone === "pos" ? "text-pos" : "text-text-secondary"}>
            {delta}
          </span>
          {deltaLabel ? <span className="text-text-tertiary"> · {deltaLabel}</span> : null}
        </span>
      )}
    </div>
  );
}
