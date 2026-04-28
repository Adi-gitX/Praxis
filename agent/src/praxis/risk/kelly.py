from __future__ import annotations

import math


def fractional_kelly(
    edge: float,
    variance: float,
    fraction: float = 0.25,
    cap: float = 1.0,
) -> float:
    """Fractional Kelly position size for a given edge / variance.

    Full-Kelly fraction is f* = mu / sigma^2 (continuous-time, log-utility
    approximation). Practitioners use a fraction of that — typically 0.25
    or 0.5 — because mu is estimated with noise and full-Kelly is brutal
    on the downside.

    Returns a position size in [-cap, cap]. Negative edge -> negative size
    (i.e. short). Zero or negative variance -> zero size.
    """
    if variance <= 0 or not math.isfinite(variance):
        return 0.0
    if not math.isfinite(edge):
        return 0.0
    full = edge / variance
    sized = fraction * full
    if sized > cap:
        return cap
    if sized < -cap:
        return -cap
    return sized
