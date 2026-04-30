"use client";

import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { base, baseSepolia } from "wagmi/chains";

/**
 * Wagmi + RainbowKit config for the /vault page.
 *
 * Uses Base Sepolia for the demo (no real money, public faucets).
 * To switch to mainnet, swap chains and inject the deployed `PraxisVault`
 * address via NEXT_PUBLIC_VAULT_ADDRESS_MAINNET.
 */
export const wagmiConfig = getDefaultConfig({
  appName: "Praxis",
  projectId:
    process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID ??
    "00000000000000000000000000000000",
  chains: [baseSepolia, base],
  ssr: true,
});

export const VAULT_ADDRESSES: Record<number, `0x${string}` | undefined> = {
  [baseSepolia.id]:
    (process.env.NEXT_PUBLIC_VAULT_ADDRESS_TESTNET as `0x${string}` | undefined) ?? undefined,
  [base.id]:
    (process.env.NEXT_PUBLIC_VAULT_ADDRESS_MAINNET as `0x${string}` | undefined) ?? undefined,
};

export const USDC_ADDRESSES: Record<number, `0x${string}`> = {
  [baseSepolia.id]: "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
  [base.id]: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
};
