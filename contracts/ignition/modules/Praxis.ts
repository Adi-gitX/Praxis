import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

const ONE_HOUR = 60 * 60;

export default buildModule("Praxis", (m) => {
  const admin = m.getAccount(0);
  const guardian = m.getAccount(0);
  const writer = m.getAccount(0);

  const baseAsset = m.getParameter<string>("baseAsset");
  const vaultName = m.getParameter<string>("vaultName", "Praxis Vault");
  const vaultSymbol = m.getParameter<string>("vaultSymbol", "pVAULT");
  const unhaltDelay = m.getParameter<number>("unhaltDelay", 24 * ONE_HOUR);

  const emergency = m.contract("EmergencyPause", [admin, guardian, unhaltDelay]);
  const registry = m.contract("StrategyRegistry", []);
  const oracle = m.contract("RiskOracle", [admin, writer]);
  const vault = m.contract("PraxisVault", [
    baseAsset,
    vaultName,
    vaultSymbol,
    admin,
    emergency,
  ]);

  return { emergency, registry, oracle, vault };
});
