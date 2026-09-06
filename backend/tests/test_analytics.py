import json
import math

import pandas as pd
import pytest

from app.analytics import build_summary
from app.analytics import indicators, risk, volatility
from app.analytics.returns import cagr, periods_per_year, total_return
from tests.conftest import make_gbm


class TestVolatility:
    @pytest.mark.parametrize(
        "estimator,uses_frame",
        [
            (volatility.close_to_close, False),
            (volatility.parkinson, True),
            (volatility.garman_klass, True),
            (volatility.rogers_satchell, True),
        ],
    )
    def test_recovers_known_sigma(self, gbm_daily, estimator, uses_frame):
        """Every estimator should land near the sigma the data was built with."""
        arg = gbm_daily if uses_frame else gbm_daily["close"]
        estimate = estimator(arg, "1d")
        assert estimate == pytest.approx(0.60, abs=0.12), estimator.__name__

    def test_flat_price_has_zero_volatility(self, flat_daily):
        assert volatility.close_to_close(flat_daily["close"], "1d") == pytest.approx(0.0)
        assert volatility.parkinson(flat_daily, "1d") == pytest.approx(0.0)

    def test_too_short_returns_none(self):
        one_bar = make_gbm(n=1)
        assert volatility.close_to_close(one_bar["close"], "1d") is None
        assert volatility.parkinson(one_bar, "1d") is None

    def test_annualisation_scales_with_interval(self, gbm_daily):
        """The same bars read as hourly imply a much larger annual figure."""
        daily = volatility.close_to_close(gbm_daily["close"], "1d")
        hourly = volatility.close_to_close(gbm_daily["close"], "1h")
        assert hourly == pytest.approx(daily * math.sqrt(24), rel=1e-9)

    def test_ewma_rejects_invalid_decay(self, gbm_daily):
        with pytest.raises(ValueError):
            volatility.ewma(gbm_daily["close"], "1d", lam=1.5)


class TestRisk:
    def test_drawdown_is_negative_and_bounded(self, gbm_daily):
        result = risk.analyse_drawdown(gbm_daily["close"])
        assert -1.0 <= result.max_drawdown <= 0.0
        assert result.peak_at <= result.trough_at

    def test_flat_price_has_no_drawdown(self, flat_daily):
        assert risk.analyse_drawdown(flat_daily["close"]).max_drawdown == pytest.approx(0.0)

    def test_cvar_is_never_milder_than_var(self, gbm_daily):
        """Expected shortfall averages the tail *beyond* VaR, so it must be worse."""
        for confidence in (0.90, 0.95, 0.99):
            var = risk.value_at_risk(gbm_daily["close"], confidence)
            cvar = risk.conditional_value_at_risk(gbm_daily["close"], confidence)
            assert cvar <= var + 1e-12, confidence

    def test_deeper_confidence_means_worse_var(self, gbm_daily):
        assert risk.value_at_risk(gbm_daily["close"], 0.99) <= risk.value_at_risk(
            gbm_daily["close"], 0.95
        )

    def test_sortino_exceeds_sharpe_for_upward_drift(self):
        """Sortino ignores upside vol, so a rising series scores higher on it."""
        rising = make_gbm(n=900, sigma=0.4, mu=0.9, seed=3)["close"]
        assert risk.sortino_ratio(rising, "1d") > risk.sharpe_ratio(rising, "1d")

    def test_flat_price_yields_no_ratios(self, flat_daily):
        assert risk.sharpe_ratio(flat_daily["close"], "1d") is None
        assert risk.sortino_ratio(flat_daily["close"], "1d") is None


class TestIndicators:
    def test_rsi_stays_in_range(self, gbm_daily):
        values = indicators.rsi(gbm_daily["close"]).dropna()
        assert values.between(0, 100).all()

    def test_rsi_of_a_pure_uptrend_is_100(self):
        rising = pd.Series(range(1, 60), dtype=float)
        assert indicators.rsi(rising).iloc[-1] == pytest.approx(100.0)

    def test_atr_is_non_negative(self, gbm_daily):
        assert (indicators.atr(gbm_daily).dropna() >= 0).all()

    def test_bollinger_bands_are_ordered(self, gbm_daily):
        bands = indicators.bollinger(gbm_daily["close"]).dropna()
        assert (bands["lower"] <= bands["middle"]).all()
        assert (bands["middle"] <= bands["upper"]).all()

    def test_range_position_is_a_fraction(self, gbm_daily):
        position = indicators.range_position(gbm_daily["close"])["position"]
        assert 0.0 <= position <= 1.0


class TestReturns:
    def test_total_and_cagr_agree_in_sign(self, gbm_daily):
        assert (total_return(gbm_daily["close"]) > 0) == (cagr(gbm_daily["close"], "1d") > 0)

    def test_periods_per_year(self):
        assert periods_per_year("1d") == pytest.approx(365.0)
        assert periods_per_year("1h") == pytest.approx(365 * 24)
        with pytest.raises(ValueError):
            periods_per_year("1y")


class TestSummary:
    def test_payload_is_json_safe(self, gbm_daily):
        """allow_nan=False is the point: NaN would silently produce invalid JSON."""
        payload = build_summary(gbm_daily, "1d", "TEST")
        json.dumps(payload, allow_nan=False)

    def test_short_history_degrades_to_nulls(self):
        """A 10-bar coin must not fabricate a 90-day volatility number."""
        payload = build_summary(make_gbm(n=10), "1d", "NEW")
        assert payload["volatility"]["realized"]["90d"] is None
        assert payload["volatility"]["realized"]["all"] is not None
        json.dumps(payload, allow_nan=False)

    def test_flat_price_is_json_safe(self, flat_daily):
        json.dumps(build_summary(flat_daily, "1d", "FLAT"), allow_nan=False)

    def test_reports_the_window_it_covered(self, gbm_daily):
        payload = build_summary(gbm_daily, "1d", "TEST")
        assert payload["bars"] == len(gbm_daily)
        assert payload["period_start"] < payload["period_end"]
