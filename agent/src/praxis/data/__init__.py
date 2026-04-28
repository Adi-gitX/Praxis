"""Data ingestion — exchange API loaders, all disk-cached for reproducibility."""
from praxis.data.ccxt_binance import BinanceLoader, fetch_btcusdt_1h

__all__ = ["BinanceLoader", "fetch_btcusdt_1h"]
