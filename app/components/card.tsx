import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export function Card({
  label,
  right,
  children,
  className,
  bodyClassName,
}: {
  label?: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section className={cn("bg-bg-elevated border border-border-subtle rounded-lg overflow-hidden", className)}>
      {(label || right) && (
        <header className="h-9 px-4 flex items-center justify-between border-b border-border-subtle bg-bg-base/40">
          <span className="label">{label}</span>
          {right}
        </header>
      )}
      <div className={cn("p-4", bodyClassName)}>{children}</div>
    </section>
  );
}
