"""Binance OHLCV loader via ccxt — paginates, caches, deterministic.

Public klines do not require an API key. Rate limit is generous; we paginate
in 1000-bar chunks and persist each window to a parquet under .praxis_cache/.
A second call with the same `(symbol, timeframe, start, end)` is offline.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

_TF_MS = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}


@dataclass
class BinanceLoader:
    """Spot OHLCV from Binance via ccxt. Returns a wide-format DataFrame indexed
    by UTC timestamp; columns are open / high / low / close / volume."""

    cache_dir: Path = Path(".praxis_cache/binance")
    rate_limit_ms: int = 500

    def __post_init__(self) -> None:
        self.cache_dir = Path(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(
        self,
        symbol: str,
        timeframe: str,
        start: str,
        end: str,
    ) -> pd.DataFrame:
        cache_path = self._cache_path(symbol, timeframe, start, end)
        if cache_path.exists():
            return pd.read_parquet(cache_path)

        try:
            import ccxt  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "ccxt is not installed; add it to dev deps or run with cached data."
            ) from exc

        exchange = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "spot"}})
        if timeframe not in _TF_MS:
            raise ValueError(f"Unsupported timeframe '{timeframe}'.")
        bar_ms = _TF_MS[timeframe]
        start_ms = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp() * 1000)
        end_ms = int(datetime.fromisoformat(end).replace(tzinfo=timezone.utc).timestamp() * 1000)

        rows: list[list[float]] = []
        cursor = start_ms
        log.info("Fetching %s %s %s..%s from Binance", symbol, timeframe, start, end)
        while cursor < end_ms:
            chunk = exchange.fetch_ohlcv(
                symbol, timeframe=timeframe, since=cursor, limit=1000
            )
            if not chunk:
                break
            rows.extend(chunk)
            last_ts = chunk[-1][0]
            if last_ts <= cursor:
                break
            cursor = last_ts + bar_ms
            time.sleep(self.rate_limit_ms / 1000.0)

        if not rows:
            raise RuntimeError(f"Binance returned no data for {symbol} {timeframe}.")

        df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
        df = df.set_index("ts").sort_index()
        df = df[~df.index.duplicated(keep="last")]
        df = df.loc[df.index <= pd.Timestamp(end_ms, unit="ms", tz="UTC")]
        df.to_parquet(cache_path)
        return df

    def _cache_path(self, symbol: str, timeframe: str, start: str, end: str) -> Path:
        safe = symbol.replace("/", "_")
        return self.cache_dir / f"{safe}_{timeframe}_{start}_{end}.parquet"


def fetch_btcusdt_1h(months: int = 24, end: str | None = None) -> pd.DataFrame:
    """Convenience wrapper: BTC/USDT 1h bars covering the last `months` months."""
    end_dt = datetime.now(tz=timezone.utc) if end is None else datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
    end_iso = end_dt.strftime("%Y-%m-%d")
    start_dt = end_dt - pd.Timedelta(days=months * 30)
    start_iso = start_dt.strftime("%Y-%m-%d")
    return BinanceLoader().fetch("BTC/USDT", "1h", start_iso, end_iso)
