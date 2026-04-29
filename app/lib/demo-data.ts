// Deterministic seeded demo data — keeps the UI alive without a backend.
// The seed is fixed so every page render produces identical numbers, which
// matters because we don't want to mislead a reviewer with random equity
// curves on every refresh.

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gauss(rng: () => number): number {
  const u = 1 - rng();
  const v = rng();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

export type EquityPoint = { ts: string; equity: number; benchmark: number; drawdown: number };

export function buildEquityCurve(
  days: number = 365,
  initial: number = 1_000_000,
  drift: number = 0.0009,
  vol: number = 0.012,
  seed: number = 42,
): EquityPoint[] {
  const rng = mulberry32(seed);
  const out: EquityPoint[] = [];
  let equity = initial;
  let benchmark = initial;
  let peak = initial;
  const start = new Date(Date.UTC(2025, 0, 1));
  for (let i = 0; i < days; i++) {
    equity *= 1 + drift + vol * gauss(rng);
    benchmark *= 1 + 0.0005 + 0.018 * gauss(rng); // higher vol benchmark
    if (equity > peak) peak = equity;
    const drawdown = (equity / peak) - 1;
    const ts = new Date(start.getTime() + i * 86400000).toISOString().slice(0, 10);
    out.push({ ts, equity, benchmark, drawdown });
  }
  return out;
}

export type SignalPoint = {
  name: string;
  asset: string;
  value: number;
  zScore: number;
};

export function snapshotSignals(seed: number = 11): SignalPoint[] {
  const rng = mulberry32(seed);
  const assets = ["BTC", "ETH", "SOL", "ARB"];
  const names = ["momentum_60", "zscore_60", "realized_vol_30", "funding_basis"];
  const out: SignalPoint[] = [];
  for (const asset of assets) {
    for (const name of names) {
      const value = (rng() * 2 - 1) * 0.5;
      out.push({ name, asset, value, zScore: gauss(rng) });
    }
  }
  return out;
}

export type Position = {
  asset: string;
  quantity: number;
  avgPrice: number;
  mark: number;
  pnl: number;
  pnlPct: number;
  weight: number;
};

export function snapshotPositions(equity: number, seed: number = 7): Position[] {
  const rng = mulberry32(seed);
  const rows: Position[] = [];
  const assets = [
    { asset: "BTC", price: 67_842.13 },
    { asset: "ETH", price: 3_412.07 },
    { asset: "SOL", price: 178.94 },
    { asset: "ARB", price: 0.7613 },
  ];
  for (const a of assets) {
    const weight = 0.05 + rng() * 0.20;
    const notional = equity * weight;
    const qty = notional / a.price;
    const mark = a.price * (1 + (rng() - 0.5) * 0.04);
    const pnl = qty * (mark - a.price);
    rows.push({
      asset: a.asset,
      quantity: qty,
      avgPrice: a.price,
      mark,
      pnl,
      pnlPct: pnl / notional,
      weight,
    });
  }
  return rows;
}

export type DecisionRow = {
  ts: string;
  regime: "trending" | "ranging" | "high_vol" | "crisis";
  strategy: string;
  asset: string;
  action: "BUY" | "SELL" | "FLAT";
  notional: number;
  reason: string;
  passed: boolean;
};

export function recentDecisions(seed: number = 19): DecisionRow[] {
  const rng = mulberry32(seed);
  const regimes: DecisionRow["regime"][] = ["trending", "ranging", "high_vol", "crisis"];
  const strategies = ["trend_following", "stat_arb", "vol_target"];
  const assets = ["BTC", "ETH", "SOL", "ARB"];
  const actions: DecisionRow["action"][] = ["BUY", "SELL", "FLAT"];
  const reasons = [
    "momentum_60 cross +1σ",
    "spread_z > 2.0 (BTC/ETH)",
    "vol target rebalance",
    "drawdown 4.21% — under cap",
    "funding basis flip",
    "regime: trending",
  ];
  const now = Date.now();
  const out: DecisionRow[] = [];
  for (let i = 0; i < 24; i++) {
    const ts = new Date(now - i * 1800_000).toISOString().slice(11, 19);
    out.push({
      ts,
      regime: regimes[Math.floor(rng() * regimes.length)],
      strategy: strategies[Math.floor(rng() * strategies.length)],
      asset: assets[Math.floor(rng() * assets.length)],
      action: actions[Math.floor(rng() * actions.length)],
      notional: rng() * 250_000,
      reason: reasons[Math.floor(rng() * reasons.length)],
      passed: rng() > 0.05,
    });
  }
  return out;
}

export function distributionFromCurve(curve: EquityPoint[]): number[] {
  const out: number[] = [];
  for (let i = 1; i < curve.length; i++) {
    out.push(curve[i].equity / curve[i - 1].equity - 1);
  }
  return out;
}

export function rollingSharpe(curve: EquityPoint[], window: number = 30): { ts: string; sharpe: number }[] {
  const returns: number[] = [];
  for (let i = 1; i < curve.length; i++) {
    returns.push(curve[i].equity / curve[i - 1].equity - 1);
  }
  const out: { ts: string; sharpe: number }[] = [];
  for (let i = window; i < returns.length; i++) {
    const slice = returns.slice(i - window, i);
    const mean = slice.reduce((a, b) => a + b, 0) / slice.length;
    const variance = slice.reduce((a, b) => a + (b - mean) ** 2, 0) / slice.length;
    const std = Math.sqrt(variance);
    const sharpe = std > 0 ? (mean / std) * Math.sqrt(365) : 0;
    out.push({ ts: curve[i].ts, sharpe });
  }
  return out;
}

export type Metrics = {
  sharpe: number;
  sortino: number;
  calmar: number;
  maxDrawdown: number;
  totalReturn: number;
  hitRate: number;
  turnover: number;
  dsr: number;
  psr: number;
  trades: number;
};

export function metricsFromCurve(curve: EquityPoint[], trades: number = 642): Metrics {
  const returns: number[] = [];
  for (let i = 1; i < curve.length; i++) {
    returns.push(curve[i].equity / curve[i - 1].equity - 1);
  }
  const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
  const variance = returns.reduce((a, b) => a + (b - mean) ** 2, 0) / returns.length;
  const std = Math.sqrt(variance);
  const sharpe = std > 0 ? (mean / std) * Math.sqrt(365) : 0;

  const downside = returns.filter((r) => r < 0);
  const downsideStd = downside.length
    ? Math.sqrt(downside.reduce((a, b) => a + b * b, 0) / downside.length)
    : 0;
  const sortino = downsideStd > 0 ? (mean / downsideStd) * Math.sqrt(365) : 0;

  let peak = curve[0].equity;
  let maxDD = 0;
  for (const p of curve) {
    if (p.equity > peak) peak = p.equity;
    const dd = (peak - p.equity) / peak;
    if (dd > maxDD) maxDD = dd;
  }
  const totalReturn = curve[curve.length - 1].equity / curve[0].equity - 1;
  const annReturn = Math.pow(1 + mean, 365) - 1;
  const calmar = maxDD > 0 ? annReturn / maxDD : 0;
  const hitRate = returns.filter((r) => r > 0).length / returns.length;

  const skew = returns.reduce((a, b) => a + (b - mean) ** 3, 0) / (returns.length * std ** 3);
  const kurt = returns.reduce((a, b) => a + (b - mean) ** 4, 0) / (returns.length * std ** 4) - 3;
  const sr = sharpe / Math.sqrt(365);
  const denom = Math.sqrt((1 - skew * sr + ((kurt - 1) / 4) * sr * sr) / (returns.length - 1));
  const psr = denom > 0 ? Math.min(0.999, Math.max(0, normalCDF(sr / denom))) : 0;
  const dsr = Math.max(0, psr - 0.05); // crude deflation: subtract 5pts for trial bias

  return {
    sharpe,
    sortino,
    calmar,
    maxDrawdown: maxDD,
    totalReturn,
    hitRate,
    turnover: 4.21,
    dsr,
    psr,
    trades,
  };
}

function normalCDF(x: number): number {
  // Abramowitz/Stegun 7.1.26
  const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741;
  const a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
  const sign = x < 0 ? -1 : 1;
  const ax = Math.abs(x) / Math.sqrt(2);
  const t = 1 / (1 + p * ax);
  const y = 1 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-ax * ax);
  return 0.5 * (1 + sign * y);
}
