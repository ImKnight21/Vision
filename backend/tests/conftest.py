import numpy as np
import pandas as pd
import pytest


def make_gbm(n=800, sigma=0.60, mu=0.10, seed=7, freq="D", ppy=365.0, substeps=1024):
    """OHLCV frame from geometric Brownian motion with a known annualised sigma.

    Each bar is simulated as `substeps` sub-intervals and the high/low are the
    true extremes of that path. Faking them as a wiggle around the open/close
    would understate the intrabar range, and the range-based estimators
    (Parkinson, Garman-Klass, Rogers-Satchell) read exactly that range — they
    would then look biased when the bug was in the fixture.

    `substeps` is deliberately large: a discretely sampled path always misses a
    little of the continuous high and low, and at 64 substeps that bias alone
    reads as a 10% volatility shortfall.
    """
    rng = np.random.default_rng(seed)
    dt = 1.0 / (ppy * substeps)
    steps = rng.normal((mu - 0.5 * sigma**2) * dt, sigma * np.sqrt(dt), n * substeps)
    path = 100.0 * np.exp(np.cumsum(steps))

    bars = path.reshape(n, substeps)
    open_ = np.concatenate([[100.0], bars[:-1, -1]])
    close = bars[:, -1]
    # The open belongs to the bar's range too, so fold it in before the extremes.
    with_open = np.column_stack([open_, bars])

    index = pd.date_range("2023-01-01", periods=n, freq=freq, tz="UTC")
    return pd.DataFrame(
        {
            "open": open_,
            "high": with_open.max(axis=1),
            "low": with_open.min(axis=1),
            "close": close,
            "volume": rng.uniform(1e3, 1e4, n),
        },
        index=index,
    )


@pytest.fixture
def gbm_daily():
    return make_gbm()


@pytest.fixture
def flat_daily():
    """A price that never moves — the degenerate case every estimator must survive."""
    index = pd.date_range("2024-01-01", periods=200, freq="D", tz="UTC")
    return pd.DataFrame(
        {"open": 50.0, "high": 50.0, "low": 50.0, "close": 50.0, "volume": 1.0},
        index=index,
    )
