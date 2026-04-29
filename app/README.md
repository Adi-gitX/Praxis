# praxis-app

Operator terminal for Praxis. Bloomberg-meets-Linear: dense grids, sparklines,
crosshair tooltips, four-decimal numbers, no rounded marketing cards.

## Pages

| Route          | Surface                                                              |
|----------------|----------------------------------------------------------------------|
| `/`            | Landing — wordmark, tagline, live stats ticker                       |
| `/terminal`    | Equity curve · positions · signal panel · decision log               |
| `/strategies`  | Per-strategy backtest + live performance                             |
| `/backtest`    | Interactive backtest runner                                          |
| `/risk`        | Exposure, VaR, correlation heatmap, drawdown distance to killswitch  |
| `/vault`       | Deposit/withdraw to the ERC-4626 vault (wagmi)                       |

## Run

```bash
yarn install
yarn dev
```
