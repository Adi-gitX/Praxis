import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";

export const metadata: Metadata = {
  title: "praxis · theory becomes execution",
  description:
    "Praxis — a research framework for autonomous quantitative trading on on-chain markets. Walk-forward backtesting, regime-aware execution, reproducible alpha discovery.",
  metadataBase: new URL("https://praxis.local"),
  openGraph: {
    title: "praxis",
    description: "theory becomes execution",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="bg-bg-base text-text-primary min-h-screen antialiased">{children}</body>
    </html>
  );
}
