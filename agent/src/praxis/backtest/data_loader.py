from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

from praxis.data.ccxt_binance import BinanceLoader

log = logging.getLogger(__name__)

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "MATIC": "matic-network",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "ARB": "arbitrum",
    "OP": "optimism",
}

BINANCE_PAIRS = {
    "BTC": "BTC/USDT",
    "ETH": "ETH/USDT",
    "SOL": "SOL/USDT",
    "AVAX": "AVAX/USDT",
    "LINK": "LINK/USDT",
    "ARB": "ARB/USDT",
    "OP": "OP/USDT",
    "MATIC": "MATIC/USDT",
}


@dataclass
class BinanceDailyLoader:
    """Default historical loader: Binance daily klines via ccxt.

    No API key required for public klines. Cached to parquet under
    `.praxis_cache/binance/`. This is the default loader for
    `praxis backtest` because it is reproducible offline after the first
    fetch and does not require third-party credentials.
    """

    inner: BinanceLoader = field(default_factory=lambda: BinanceLoader(cache_dir=Path(".praxis_cache/binance")))

    def load(self, symbols: list[str], start: str, end: str) -> pd.DataFrame:
        frames: dict[str, pd.Series] = {}
        for sym in symbols:
            pair = BINANCE_PAIRS.get(sym.upper())
            if pair is None:
                raise KeyError(
                    f"No Binance pair mapped for symbol '{sym}'. "
                    f"Add it to BINANCE_PAIRS or use --prices-csv."
                )
            df = self.inner.fetch(pair, "1d", start, end)
            close = df["close"].copy()
            idx = pd.DatetimeIndex(close.index)
            if idx.tz is not None:
                idx = idx.tz_convert(None)
            close.index = idx
            close.name = sym
            frames[sym] = close
        out = pd.DataFrame(frames).sort_index()
        out = out.dropna(how="all").ffill()
        if out.empty:
            raise RuntimeError(
                f"No price data loaded for {symbols} in {start}..{end}."
            )
        return out


@dataclass
class CoinGeckoLoader:
    """Optional alternative loader using CoinGecko's API.

    The free tier's `/market_chart/range` endpoint now requires a demo API
    key as of 2025; pass it via the `COINGECKO_API_KEY` env var. Without a
    key this loader will return 401 and you should use `BinanceDailyLoader`
    instead.
    """

    cache_dir: Path = Path(".praxis_cache/coingecko")
    base_url: str = "https://api.coingecko.com/api/v3"
    request_timeout: float = 20.0
    pause_between_calls: float = 1.5
    api_key: str | None = None

    def __post_init__(self) -> None:
        self.cache_dir = Path(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if self.api_key is None:
            self.api_key = os.getenv("COINGECKO_API_KEY")

    def load(self, symbols: list[str], start: str, end: str) -> pd.DataFrame:
        frames: dict[str, pd.Series] = {}
        for sym in symbols:
            frames[sym] = self._load_one(sym, start, end)
        df = pd.DataFrame(frames).sort_index()
        df = df.dropna(how="all")
        if df.empty:
            raise RuntimeError(
                f"No price data loaded for {symbols} in {start}..{end}."
            )
        return df.ffill()

    def _load_one(self, symbol: str, start: str, end: str) -> pd.Series:
        cache_path = self.cache_dir / f"{symbol}_{start}_{end}.csv"
        if cache_path.exists():
            return pd.read_csv(cache_path, index_col=0, parse_dates=True).iloc[:, 0]

        cg_id = COINGECKO_IDS.get(symbol.upper())
        if cg_id is None:
            raise KeyError(
                f"Unknown CoinGecko id for symbol '{symbol}'. "
                f"Add it to COINGECKO_IDS or override `load`."
            )
        from_ts = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp())
        to_ts = int(datetime.fromisoformat(end).replace(tzinfo=timezone.utc).timestamp())

        params = {"vs_currency": "usd", "from": str(from_ts), "to": str(to_ts)}
        headers = {"x-cg-demo-api-key": self.api_key} if self.api_key else {}
        url = f"{self.base_url}/coins/{cg_id}/market_chart/range"
        log.info("CoinGecko fetch: %s %s..%s", symbol, start, end)
        response = httpx.get(url, params=params, headers=headers, timeout=self.request_timeout)
        response.raise_for_status()
        prices = response.json().get("prices", [])
        if not prices:
            raise RuntimeError(f"CoinGecko returned no prices for {symbol}")

        series = pd.Series(
            {pd.Timestamp(p[0], unit="ms", tz="UTC").normalize().tz_convert(None): p[1] for p in prices}
        )
        series = series[~series.index.duplicated(keep="last")].sort_index()
        series.name = symbol
        series.to_csv(cache_path)
        time.sleep(self.pause_between_calls)
        return series


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a wide-format CSV: index column is timestamp, remaining columns are
    asset close prices. Useful for plugging in your own historical dataset.
    """
    df = pd.read_csv(path, index_col=0, parse_dates=True).sort_index()
    return df.ffill()
