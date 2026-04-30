"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Wordmark } from "@/components/wordmark";
import { StatusPill } from "@/components/status-pill";
import { cn } from "@/lib/utils";

const ITEMS = [
  { href: "/terminal", label: "terminal" },
  { href: "/strategies", label: "strategies" },
  { href: "/backtest", label: "backtest" },
  { href: "/runs", label: "runs" },
  { href: "/regime", label: "regime" },
  { href: "/risk", label: "risk" },
  { href: "/vault", label: "vault" },
  { href: "/about/methodology", label: "methodology" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <header className="border-b border-border-subtle bg-bg-base sticky top-0 z-30">
      <div className="px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center">
            <Wordmark size="md" />
          </Link>
          <nav className="hidden md:flex items-center gap-1">
            {ITEMS.map((item) => {
              const active = pathname?.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "px-3 py-1.5 text-sm mono lowercase transition-colors",
                    active
                      ? "text-text-primary border-b border-accent"
                      : "text-text-secondary hover:text-text-primary",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden sm:inline-block text-2xs label">env · base-sepolia</span>
          <StatusPill status="paper" />
        </div>
      </div>
    </header>
  );
}
