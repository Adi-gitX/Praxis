"use client";

import { ConnectButton } from "@rainbow-me/rainbowkit";
import { useEffect, useMemo, useState } from "react";
import { parseUnits, formatUnits } from "viem";
import {
  useAccount,
  useChainId,
  useReadContract,
  useWaitForTransactionReceipt,
  useWriteContract,
} from "wagmi";

import { Card } from "@/components/card";
import { StatusPill } from "@/components/status-pill";
import { USDC_ADDRESSES, VAULT_ADDRESSES } from "@/lib/wagmi";
import { fmtNum, fmtUSD } from "@/lib/format";
import { cn } from "@/lib/utils";

const ERC20_ABI = [
  {
    type: "function",
    name: "balanceOf",
    stateMutability: "view",
    inputs: [{ name: "account", type: "address" }],
    outputs: [{ type: "uint256" }],
  },
  {
    type: "function",
    name: "allowance",
    stateMutability: "view",
    inputs: [
      { name: "owner", type: "address" },
      { name: "spender", type: "address" },
    ],
    outputs: [{ type: "uint256" }],
  },
  {
    type: "function",
    name: "approve",
    stateMutability: "nonpayable",
    inputs: [
      { name: "spender", type: "address" },
      { name: "amount", type: "uint256" },
    ],
    outputs: [{ type: "bool" }],
  },
  {
    type: "function",
    name: "decimals",
    stateMutability: "view",
    inputs: [],
    outputs: [{ type: "uint8" }],
  },
] as const;

const VAULT_ABI = [
  {
    type: "function",
    name: "deposit",
    stateMutability: "nonpayable",
    inputs: [
      { name: "assets", type: "uint256" },
      { name: "receiver", type: "address" },
    ],
    outputs: [{ type: "uint256" }],
  },
  {
    type: "function",
    name: "redeem",
    stateMutability: "nonpayable",
    inputs: [
      { name: "shares", type: "uint256" },
      { name: "receiver", type: "address" },
      { name: "owner", type: "address" },
    ],
    outputs: [{ type: "uint256" }],
  },
  {
    type: "function",
    name: "balanceOf",
    stateMutability: "view",
    inputs: [{ name: "account", type: "address" }],
    outputs: [{ type: "uint256" }],
  },
  {
    type: "function",
    name: "totalAssets",
    stateMutability: "view",
    inputs: [],
    outputs: [{ type: "uint256" }],
  },
  {
    type: "function",
    name: "convertToAssets",
    stateMutability: "view",
    inputs: [{ name: "shares", type: "uint256" }],
    outputs: [{ type: "uint256" }],
  },
] as const;

export function VaultFlow() {
  const { address, isConnected } = useAccount();
  const chainId = useChainId();
  const [tab, setTab] = useState<"deposit" | "withdraw">("deposit");
  const [amount, setAmount] = useState("");

  const vault = VAULT_ADDRESSES[chainId];
  const usdc = USDC_ADDRESSES[chainId];

  const decimalsRead = useReadContract({
    address: usdc,
    abi: ERC20_ABI,
    functionName: "decimals",
    query: { enabled: Boolean(usdc) },
  });
  const decimals = decimalsRead.data ?? 6;

  const usdcBal = useReadContract({
    address: usdc,
    abi: ERC20_ABI,
    functionName: "balanceOf",
    args: address ? [address] : undefined,
    query: { enabled: Boolean(address && usdc) },
  });
  const allowance = useReadContract({
    address: usdc,
    abi: ERC20_ABI,
    functionName: "allowance",
    args: address && vault ? [address, vault] : undefined,
    query: { enabled: Boolean(address && vault && usdc) },
  });
  const shares = useReadContract({
    address: vault,
    abi: VAULT_ABI,
    functionName: "balanceOf",
    args: address ? [address] : undefined,
    query: { enabled: Boolean(address && vault) },
  });
  const totalAssets = useReadContract({
    address: vault,
    abi: VAULT_ABI,
    functionName: "totalAssets",
    query: { enabled: Boolean(vault) },
  });
  const shareValue = useReadContract({
    address: vault,
    abi: VAULT_ABI,
    functionName: "convertToAssets",
    args: shares.data !== undefined ? [shares.data] : undefined,
    query: { enabled: Boolean(vault && shares.data !== undefined) },
  });

  const { writeContract, data: txHash, isPending: isWriting } = useWriteContract();
  const { isLoading: isMining, isSuccess: txConfirmed } = useWaitForTransactionReceipt({
    hash: txHash,
  });

  useEffect(() => {
    if (txConfirmed) {
      usdcBal.refetch();
      allowance.refetch();
      shares.refetch();
      totalAssets.refetch();
      shareValue.refetch();
      setAmount("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [txConfirmed]);

  const parsedAmount = useMemo(() => {
    if (!amount) return 0n;
    try {
      return parseUnits(amount, decimals);
    } catch {
      return 0n;
    }
  }, [amount, decimals]);

  const needsApproval =
    tab === "deposit" && parsedAmount > 0n && (allowance.data ?? 0n) < parsedAmount;

  if (!vault) {
    return (
      <Card label="vault not deployed">
        <p className="text-sm text-text-secondary">
          The PraxisVault contract has not been deployed on the connected chain. Set{" "}
          <code className="mono text-accent">NEXT_PUBLIC_VAULT_ADDRESS_TESTNET</code> at
          build time once you run{" "}
          <code className="mono">npx hardhat ignition deploy</code> on Base Sepolia.
        </p>
      </Card>
    );
  }

  if (!isConnected) {
    return (
      <Card label="connect wallet">
        <p className="text-sm text-text-secondary mb-4">
          Connect a wallet on Base Sepolia to deposit USDC into the vault.
        </p>
        <ConnectButton showBalance={false} />
      </Card>
    );
  }

  const usdcBalance = usdcBal.data ?? 0n;
  const userShares = shares.data ?? 0n;
  const userValue = shareValue.data ?? 0n;

  const onSubmit = () => {
    if (parsedAmount === 0n) return;
    if (tab === "deposit") {
      if (needsApproval) {
        writeContract({
          address: usdc,
          abi: ERC20_ABI,
          functionName: "approve",
          args: [vault, parsedAmount],
        });
        return;
      }
      writeContract({
        address: vault,
        abi: VAULT_ABI,
        functionName: "deposit",
        args: [parsedAmount, address!],
      });
    } else {
      writeContract({
        address: vault,
        abi: VAULT_ABI,
        functionName: "redeem",
        args: [parsedAmount, address!, address!],
      });
    }
  };

  const ctaLabel = isWriting
    ? "confirm in wallet…"
    : isMining
    ? "waiting for tx…"
    : tab === "deposit"
    ? needsApproval
      ? "approve usdc"
      : "deposit usdc"
    : "redeem shares";

  return (
    <Card
      label={tab === "deposit" ? "deposit · usdc" : "withdraw · shares"}
      right={<StatusPill status={txHash ? (txConfirmed ? "live" : "backtest") : "paper"} />}
    >
      <div className="flex gap-2 mb-4 border-b border-border-subtle">
        {(["deposit", "withdraw"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "px-3 py-2 text-sm mono",
              tab === t
                ? "text-text-primary border-b border-accent"
                : "text-text-secondary",
            )}
          >
            {t}
          </button>
        ))}
      </div>

      <label className="block text-sm">
        <span className="label">amount {tab === "deposit" ? "(usdc)" : "(shares)"}</span>
        <input
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="0.00"
          className="mt-1 w-full bg-bg-overlay border border-border-default px-3 py-2 mono"
        />
      </label>

      <div className="mt-4 space-y-2 text-sm">
        <Row
          label="your wallet"
          value={`${fmtUSD(Number(formatUnits(usdcBalance, decimals)), 2)} USDC`}
        />
        <Row label="your shares" value={fmtNum(Number(formatUnits(userShares, 18)), 4)} />
        <Row
          label="your share value"
          value={`${fmtUSD(Number(formatUnits(userValue, decimals)), 2)} USDC`}
        />
        <Row
          label="vault TVL"
          value={`${fmtUSD(Number(formatUnits(totalAssets.data ?? 0n, decimals)), 2)} USDC`}
        />
      </div>

      <button
        onClick={onSubmit}
        disabled={parsedAmount === 0n || isWriting || isMining}
        className="mt-5 w-full px-3 py-2.5 bg-accent hover:bg-accent-hover text-bg-base mono text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {ctaLabel}
      </button>

      {txHash ? (
        <p className="mt-3 text-2xs text-text-tertiary mono break-all">tx: {txHash}</p>
      ) : null}

      <div className="mt-3 flex justify-end">
        <ConnectButton showBalance={false} chainStatus="icon" accountStatus="address" />
      </div>
    </Card>
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
