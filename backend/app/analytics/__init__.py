"""Statistical analysis of OHLCV series.

Every public function is pure: it takes a frame or series and returns plain
floats, so the numbers can be tested without touching the network.
"""

from app.analytics.summary import build_summary

__all__ = ["build_summary"]
