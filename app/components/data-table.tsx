import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export type Column<T> = {
  key: string;
  header: string;
  accessor: (row: T) => ReactNode;
  align?: "left" | "right";
  width?: string;
};

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  className,
}: {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T, i: number) => string;
  className?: string;
}) {
  return (
    <div className={cn("w-full overflow-x-auto", className)}>
      <table className="w-full text-sm tabular">
        <thead>
          <tr className="bg-bg-overlay">
            {columns.map((c) => (
              <th
                key={c.key}
                className={cn(
                  "label py-2 px-3 sticky top-0 bg-bg-overlay border-b border-border-subtle",
                  c.align === "right" ? "text-right" : "text-left",
                )}
                style={{ width: c.width }}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={rowKey(row, i)}
              className={cn(
                "border-b border-border-subtle transition-colors",
                i % 2 === 0 ? "bg-bg-base" : "bg-bg-elevated",
                "hover:bg-bg-overlay",
              )}
            >
              {columns.map((c) => (
                <td
                  key={c.key}
                  className={cn(
                    "py-2 px-3",
                    c.align === "right" ? "text-right mono" : "text-left",
                  )}
                >
                  {c.accessor(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
