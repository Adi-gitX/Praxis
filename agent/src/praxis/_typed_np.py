"""Type-safe numpy/pandas adapters.

`np.log(df)` returns a `pd.DataFrame` at runtime via ufunc dispatch, but the
combined numpy + pandas-stubs do not reflect that — mypy infers an `ndarray`
return, after which `.diff()` / `.shift()` lookups fail. The wrappers below
preserve the runtime contract explicitly so the rest of the codebase stays
strict-typed without per-call casts.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def log_df(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(np.log(df.to_numpy(dtype=float)), index=df.index, columns=df.columns)


def log_series(series: pd.Series) -> pd.Series:
    return pd.Series(np.log(series.to_numpy(dtype=float)), index=series.index, name=series.name)
