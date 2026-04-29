import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";

require("dotenv").config();

const dummyKey = "0x0000000000000000000000000000000000000000000000000000000000000001";
const walletKey = process.env.WALLET_KEY ?? dummyKey;

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.27",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      evmVersion: "cancun",
    },
  },
  networks: {
    "base-mainnet": {
      url: "https://mainnet.base.org",
      accounts: [walletKey],
      gasPrice: 1000000000,
    },
    "base-sepolia": {
      url: "https://sepolia.base.org",
      accounts: [walletKey],
      gasPrice: 1000000000,
    },
    "base-local": {
      url: "http://localhost:8545",
      accounts: [walletKey],
      gasPrice: 1000000000,
    },
  },
  etherscan: {
    apiKey: { baseSepolia: process.env.ETHERSCAN_API_KEY ?? "dummy" },
  },
  defaultNetwork: "hardhat",
};

export default config;
