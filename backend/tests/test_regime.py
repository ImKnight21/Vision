import numpy as np
import pandas as pd
import pytest

from app.analytics import liquidity, regime, relative, risk
from tests.conftest import make_gbm


def series_from(values) -> pd.Series:
    index = pd.date_range("2023-01-01", periods=len(values), freq="D", tz="UTC")
    return pd.Series(values, index=index, dtype=float)


def trending(n=600, drift=0.004, noise=0.01, seed=1) -> pd.Series:
    """A persistent path: each step keeps most of the previous one's direction."""
    rng = np.random.default_rng(seed)
    steps = np.full(n, drift) + rng.normal(0, noise, n)
    return series_from(100 * np.exp(np.cumsum(steps)))


def mean_reverting(n=600, seed=2) -> pd.Series:
    """An Ornstein-Uhlenbeck style path that keeps being pulled back to 100."""
    rng = np.random.default_rng(seed)
    values = [100.0]
    for _ in range(n - 1):
        pull = 0.25 * (100.0 - values[-1])
        values.append(max(values[-1] + pull + rng.normal(0, 2.0), 1.0))
    return series_from(values)


class TestHurst:
    def test_random_walk_sits_near_a_half(self, gbm_daily):
        assert regime.hurst_exponent(gbm_daily["close"]) == pytest.approx(0.5, abs=0.15)

    def test_trending_series_scores_higher_than_mean_reverting(self):
        """The exponent's whole purpose is to separate these two regimes."""
        assert regime.hurst_exponent(trending()) > regime.hurst_exponent(mean_reverting())

    def test_mean_reverting_series_falls_below_a_half(self):
        assert regime.hurst_exponent(mean_reverting()) < 0.5

    def test_short_history_returns_none(self):
        assert regime.hurst_exponent(make_gbm(n=60)["close"]) is None


class TestRegimeOther:
    def test_autocorrelation_detects_reversal(self):
        """A series pulled back to its mean has negative lag-1 autocorrelation."""
        assert regime.autocorrelation(mean_reverting()) < 0

    def test_autocorrelation_of_flat_price_is_none(self, flat_daily):
        assert regime.autocorrelation(flat_daily["close"]) is None

    def test_trend_strength_is_high_for_a_clean_run(self):
        assert regime.trend_strength(trending(noise=0.002), window=100) > 0.9

    def test_trend_strength_is_bounded(self, gbm_daily):
        assert 0.0 <= regime.trend_strength(gbm_daily["close"]) <= 1.0

    def test_trend_change_is_not_annualised(self):
        """A 50-bar drift must be reported over 50 bars, not compounded to a year.

        Annualising it produced figures above +1000%, which are arithmetically
        correct and analytically useless.
        """
        change = regime.trend_change(trending(drift=0.004), window=50)
        # 50 bars of 0.4% drift is roughly +22%, nowhere near a yearly figure.
        assert 0.1 < change < 0.5

    def test_volatility_percentile_is_a_fraction(self, gbm_daily):
        value = regime.volatility_percentile(gbm_daily["close"], "1d")
        assert 0.0 <= value <= 1.0

    def test_volatility_percentile_is_high_after_a_shock(self):
        """Calm history then a violent tail should place current vol near the top."""
        rng = np.random.default_rng(5)
        calm = rng.normal(0, 0.005, 400)
        wild = rng.normal(0, 0.05, 60)
        close = series_from(100 * np.exp(np.cumsum(np.concatenate([calm, wild]))))
        assert regime.volatility_percentile(close, "1d") > 0.9


class TestRiskDuration:
    def test_ulcer_index_is_non_negative(self, gbm_daily):
        assert regime is not None
        assert risk.ulcer_index(gbm_daily["close"]) >= 0

    def test_flat_price_has_no_ulcer(self, flat_daily):
        assert risk.ulcer_index(flat_daily["close"]) == pytest.approx(0.0)

    def test_a_deeper_slump_scores_worse(self):
        """Ulcer must react to depth, which max drawdown alone also does."""
        shallow = series_from([100, 98, 97, 99, 100] * 40)
        deep = series_from([100, 60, 55, 70, 100] * 40)
        assert risk.ulcer_index(deep) > risk.ulcer_index(shallow)

    def test_time_under_water_on_a_monotonic_rise(self):
        """A series making new highs every bar is never under water."""
        rising = series_from(np.linspace(100, 200, 300))
        result = risk.time_under_water(rising)
        assert result["share"] == pytest.approx(0.0)
        assert result["longest_bars"] == 0

    def test_time_under_water_tracks_the_current_streak(self):
        falling = series_from(np.concatenate([np.linspace(100, 200, 150),
                                              np.linspace(200, 120, 150)]))
        result = risk.time_under_water(falling)
        assert result["share"] > 0.4
        assert result["current_bars"] > 100

    def test_tail_ratio_above_one_when_gains_are_larger(self):
        rng = np.random.default_rng(11)
        # Positively skewed: small frequent losses, rare large gains.
        steps = rng.choice([0.30, -0.01], size=500, p=[0.1, 0.9])
        assert risk.tail_ratio(series_from(100 * np.cumprod(1 + steps))) > 1.0

    def test_omega_is_positive_and_finite(self, gbm_daily):
        assert risk.omega_ratio(gbm_daily["close"]) > 0


class TestRelative:
    def test_identical_series_are_perfectly_correlated(self, gbm_daily):
        close = gbm_daily["close"]
        result = relative.compare(close, close, "1d")
        assert result.correlation == pytest.approx(1.0)
        assert result.beta == pytest.approx(1.0)
        assert result.alpha == pytest.approx(0.0, abs=1e-9)

    def test_leveraged_series_has_beta_near_the_multiple(self, gbm_daily):
        """A series that moves twice as hard on the same shocks has beta 2."""
        benchmark = gbm_daily["close"]
        returns = np.log(benchmark).diff().fillna(0.0)
        levered = pd.Series(
            float(benchmark.iloc[0]) * np.exp(np.cumsum(returns * 2.0)),
            index=benchmark.index,
        )
        result = relative.compare(levered, benchmark, "1d")
        assert result.beta == pytest.approx(2.0, abs=0.05)
        assert result.correlation == pytest.approx(1.0, abs=0.01)

    def test_alignment_uses_shared_timestamps_only(self, gbm_daily):
        """A short history must shorten the comparison, not misalign it."""
        benchmark = gbm_daily["close"]
        short = benchmark.tail(120)
        result = relative.compare(short, benchmark, "1d")
        assert result.bars == pytest.approx(119, abs=1)

    def test_too_little_overlap_yields_nulls(self, gbm_daily):
        benchmark = gbm_daily["close"]
        result = relative.compare(benchmark.tail(10), benchmark, "1d")
        assert result.beta is None and result.correlation is None

    def test_correlation_matrix_is_symmetric_with_unit_diagonal(self, gbm_daily):
        closes = {
            "A": gbm_daily["close"],
            "B": make_gbm(seed=21)["close"],
            "C": make_gbm(seed=22)["close"],
        }
        result = relative.correlation_matrix(closes)
        matrix = result["matrix"]
        assert result["symbols"] == ["A", "B", "C"]
        for i in range(3):
            assert matrix[i][i] == pytest.approx(1.0)
            for j in range(3):
                assert matrix[i][j] == pytest.approx(matrix[j][i])


class TestLiquidity:
    def test_thin_market_is_less_liquid(self, gbm_daily):
        """Same prices, a hundredth of the volume: impact must be far higher."""
        thick = gbm_daily.copy()
        thin = gbm_daily.copy()
        thin["volume"] = thin["volume"] / 100.0
        assert liquidity.amihud_illiquidity(thin) > liquidity.amihud_illiquidity(thick)

    def test_volume_spike_shows_a_high_zscore(self, gbm_daily):
        frame = gbm_daily.copy()
        frame.iloc[-1, frame.columns.get_loc("volume")] = frame["volume"].mean() * 20
        assert liquidity.volume_zscore(frame) > 3

    def test_volume_trend_is_one_for_steady_turnover(self):
        index = pd.date_range("2024-01-01", periods=120, freq="D", tz="UTC")
        frame = pd.DataFrame(
            {"open": 10.0, "high": 10.0, "low": 10.0, "close": 10.0, "volume": 100.0},
            index=index,
        )
        assert liquidity.volume_trend(frame) == pytest.approx(1.0)

    def test_turnover_needs_a_market_cap(self, gbm_daily):
        assert liquidity.turnover(gbm_daily, None) is None
        assert liquidity.turnover(gbm_daily, 0) is None
        assert liquidity.turnover(gbm_daily, 1e9) > 0
