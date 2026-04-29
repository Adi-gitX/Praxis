# praxis-contracts

Solidity primitives that anchor the Praxis agent on-chain.

| Contract             | Purpose                                                              |
|----------------------|----------------------------------------------------------------------|
| `Vault.sol`          | ERC-4626 vault — depositors get shares, agent manages assets         |
| `StrategyRegistry.sol`| On-chain registry of approved strategies + circuit breakers          |
| `RiskOracle.sol`     | Read-only contract surfacing current risk metrics on-chain            |
| `EmergencyPause.sol` | Killswitch with timelock                                              |

## Deploy

```bash
yarn install
yarn compile
yarn deploy:base-sepolia
```
