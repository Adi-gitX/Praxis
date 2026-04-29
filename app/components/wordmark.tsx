import { cn } from "@/lib/utils";

export function Wordmark({ size = "md", className }: { size?: "sm" | "md" | "lg" | "xl"; className?: string }) {
  const sizes = {
    sm: "text-base",
    md: "text-lg",
    lg: "text-2xl",
    xl: "text-4xl",
  } as const;
  const markSize = {
    sm: "h-3 w-3",
    md: "h-4 w-4",
    lg: "h-5 w-5",
    xl: "h-7 w-7",
  } as const;
  return (
    <span className={cn("inline-flex items-center gap-2 mono lowercase tracking-tight", sizes[size], className)}>
      <svg viewBox="0 0 24 24" className={markSize[size]} aria-hidden="true">
        <polygon points="12,2 22,20 2,20" fill="var(--accent)" />
      </svg>
      <span className="text-text-primary">praxis</span>
    </span>
  );
}
