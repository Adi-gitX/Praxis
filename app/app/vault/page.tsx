import { Card } from "@/components/card";
import { Nav } from "@/components/nav";
import { StatBlock } from "@/components/stat-block";
import { StatusPill } from "@/components/status-pill";
import { VaultFlow } from "@/components/vault-flow";
import { Web3Providers } from "@/components/web3-providers";
import { fmtNum, fmtUSD } from "@/lib/format";

// wagmi/RainbowKit need a browser environment (localStorage, window). Tag
// the page dynamic so Next.js skips static prerender at build time.
export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export default function VaultPage() {
  // Static panel data — these stay seeded until the contracts are deployed
  // and indexed; the VaultFlow card on the right is fully live via wagmi.
  const aum = 4_217_512.04;
  const sharePrice = 1.0421;
  const totalShares = aum / sharePrice;

  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-6 py-8 max-w-5xl mx-auto w-full space-y-6">
        <header className="flex items-end justify-between gap-4">
          <div>
            <span className="label">vault</span>
            <h1 className="mt-1 text-2xl text-text-primary">PraxisVault · ERC-4626</h1>
            <p className="text-xs text-text-tertiary mono mt-1">
              base-sepolia · set NEXT_PUBLIC_VAULT_ADDRESS_TESTNET after deploy
            </p>
          </div>
          <StatusPill status="paper" />
        </header>

        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card label="AUM"><StatBlock label="usdc · indicative" value={fmtUSD(aum, 0)} size="sm" /></Card>
          <Card label="SHARE PRICE"><StatBlock label="convertToAssets(1e18)" value={fmtNum(sharePrice, 4)} size="sm" /></Card>
          <Card label="TOTAL SUPPLY"><StatBlock label="shares · indicative" value={fmtNum(totalShares, 0)} size="sm" /></Card>
          <Card label="EMERGENCY"><StatBlock label="halt status" value="LIVE" size="sm" tone="pos" /></Card>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-[1fr_360px] gap-4">
          <Card label="recent flow · indicative">
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
            <p className="mt-4 text-2xs text-text-tertiary leading-relaxed">
              The flow list above is indicative until an indexer is wired (v0.2 roadmap).
              The deposit/withdraw card to the right is *fully live* via wagmi + RainbowKit
              — connect a wallet on Base Sepolia and the read contracts (USDC balance,
              vault shares, share value, TVL) update from on-chain state in real time.
            </p>
          </Card>

          <Web3Providers>
            <VaultFlow />
          </Web3Providers>
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

const FLOWS = [
  { kind: "deposit", from: "0x9a…42c", amount: 50_000, tx: "0xabc1…ef" },
  { kind: "withdraw", from: "0x12…f4d", amount: 12_500, tx: "0xdef2…71" },
  { kind: "deposit", from: "0x88…1aa", amount: 175_000, tx: "0x991a…b3" },
  { kind: "deposit", from: "0x71…99e", amount: 25_000, tx: "0x5511…c0" },
];
