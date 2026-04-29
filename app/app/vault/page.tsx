"use client";

import { useState } from "react";

import { Card } from "@/components/card";
import { Nav } from "@/components/nav";
import { StatBlock } from "@/components/stat-block";
import { StatusPill } from "@/components/status-pill";
import { fmtNum, fmtUSD } from "@/lib/format";

export default function VaultPage() {
  const [tab, setTab] = useState<"deposit" | "withdraw">("deposit");
  const [amount, setAmount] = useState("");
  const aum = 4_217_512.04;
  const sharePrice = 1.0421;
  const totalShares = aum / sharePrice;
  const myShares = 14_281;
  const myValue = myShares * sharePrice;

  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-6 py-8 max-w-5xl mx-auto w-full space-y-6">
        <header className="flex items-end justify-between gap-4">
          <div>
            <span className="label">vault</span>
            <h1 className="mt-1 text-2xl text-text-primary">PraxisVault · ERC-4626</h1>
            <p className="text-xs text-text-tertiary mono mt-1">base-sepolia · proxy 0x… (placeholder)</p>
          </div>
          <StatusPill status="paper" />
        </header>

        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card label="AUM"><StatBlock label="usdc" value={fmtUSD(aum, 0)} size="sm" /></Card>
          <Card label="SHARE PRICE"><StatBlock label="convertToAssets(1e18)" value={fmtNum(sharePrice, 4)} size="sm" /></Card>
          <Card label="TOTAL SUPPLY"><StatBlock label="shares" value={fmtNum(totalShares, 0)} size="sm" /></Card>
          <Card label="EMERGENCY"><StatBlock label="halt status" value="LIVE" size="sm" tone="pos" /></Card>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-[1fr_320px] gap-4">
          <Card label="RECENT FLOW">
            <ul className="text-sm divide-y divide-border-subtle">
              {FLOWS.map((f, i) => (
                <li key={i} className="flex items-center justify-between py-2">
                  <span className={`mono ${f.kind === "deposit" ? "text-pos" : "text-neg"}`}>
                    {f.kind === "deposit" ? "+ deposit" : "- withdraw"}
                  </span>
                  <span className="text-text-secondary mono text-xs">{f.from}</span>
                  <span className="mono tabular">{fmtUSD(f.amount, 2)}</span>
                  <span className="text-text-tertiary mono text-xs">{f.tx}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card label={tab === "deposit" ? "deposit · usdc" : "withdraw · shares"}>
            <div className="flex gap-2 mb-4 border-b border-border-subtle">
              {(["deposit", "withdraw"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={
                    "px-3 py-2 text-sm mono " +
                    (tab === t
                      ? "text-text-primary border-b border-accent"
                      : "text-text-secondary")
                  }
                >
                  {t}
                </button>
              ))}
            </div>

            <label className="block text-sm">
              <span className="label">amount</span>
              <input
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="mt-1 w-full bg-bg-overlay border border-border-default px-3 py-2 mono"
              />
            </label>

            <div className="mt-4 space-y-2 text-sm">
              <Row label="your shares" value={fmtNum(myShares, 0)} />
              <Row label="your value" value={fmtUSD(myValue, 2)} />
              <Row label="share price" value={fmtNum(sharePrice, 4)} />
              <Row label="entry fee" value="0.00%" />
              <Row label="exit fee" value="0.10%" />
            </div>

            <button className="mt-5 w-full px-3 py-2.5 bg-accent hover:bg-accent-hover text-bg-base mono text-sm transition-colors">
              {tab === "deposit" ? "deposit usdc" : "withdraw shares"}
            </button>
            <p className="mt-3 text-2xs text-text-tertiary leading-relaxed">
              Wallet flow is wagmi-stubbed in this scaffold. Connect support is wired in
              `lib/wagmi` once a contract is redeployed.
            </p>
          </Card>
        </section>

        <Card label="GUARDIAN · circuit breakers">
          <ul className="text-sm grid sm:grid-cols-3 gap-4">
            <li>
              <span className="label">max drawdown</span>
              <p className="mono text-lg mt-1">25.00%</p>
              <p className="text-xs text-text-tertiary mt-1">
                Halt deposits; existing shares can still redeem. One-way trip.
              </p>
            </li>
            <li>
              <span className="label">unhalt timelock</span>
              <p className="mono text-lg mt-1">24 h</p>
              <p className="text-xs text-text-tertiary mt-1">
                Admin schedules unhalt; effective only after delay.
              </p>
            </li>
            <li>
              <span className="label">guardian</span>
              <p className="mono text-lg mt-1">multisig</p>
              <p className="text-xs text-text-tertiary mt-1">
                Has GUARDIAN_ROLE in EmergencyPause; halts on anomaly detection.
              </p>
            </li>
          </ul>
        </Card>
      </main>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-text-secondary">
      <span>{label}</span>
      <span className="mono tabular text-text-primary">{value}</span>
    </div>
  );
}

const FLOWS = [
  { kind: "deposit", from: "0x9a…42c", amount: 50_000, tx: "0xabc1…ef" },
  { kind: "withdraw", from: "0x12…f4d", amount: 12_500, tx: "0xdef2…71" },
  { kind: "deposit", from: "0x88…1aa", amount: 175_000, tx: "0x991a…b3" },
  { kind: "deposit", from: "0x71…99e", amount: 25_000, tx: "0x5511…c0" },
];
