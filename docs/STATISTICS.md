# The statistics

Every figure below is computed in [`backend/app/analytics/`](../backend/app/analytics/)
from a plain OHLCV frame, and every one is returned as a **fraction** — `0.0241`
is +2.41%. When the loaded history is too short to fill a window, the value is
`null` rather than a number computed from whatever happened to be there.

Two conventions apply throughout:

- **A year is 365 days.** Crypto trades continuously, so the ~252 trading days
  used for equities would understate every annualised figure by about 20%.
- **Windows are calendar days, not bars.** "30d volatility" spans thirty days
  whether the chart is hourly or daily; the bar count is derived from the
  interval.

---

## Volatility

All four estimators are annualised standard deviations. A value of `0.45` means
that if the last window's behaviour continued for a year, a one-standard-
deviation move would be 45%.

### Close-to-close

The textbook estimator: the sample standard deviation of log returns, scaled by
√(periods per year). It only looks at closing prices, so everything that
happened inside the bar is discarded.

Use it as the reference number. It is what everyone else quotes.

### Parkinson

Uses the bar's high and low instead of its close:

$$\sigma = \sqrt{\frac{1}{4N\ln 2}\sum \ln^2\!\left(\frac{H}{L}\right)}$$

Roughly five times more statistically efficient than close-to-close — it
converges on the true volatility with far fewer bars, which matters for a coin
that has only traded a few weeks. The trade-offs: it assumes no drift, and it
cannot see gaps between one bar's close and the next one's open.

### Garman-Klass

Uses the full OHLC bar, combining the high-low range with the open-to-close
move. The most efficient of the three when price is not trending. Like
Parkinson it assumes zero drift, so a strong trend inflates it.

### Rogers-Satchell

$$\sigma = \sqrt{\frac{1}{N}\sum \ln\!\frac{H}{C}\ln\!\frac{H}{O} + \ln\!\frac{L}{C}\ln\!\frac{L}{O}}$$

The only range estimator that stays unbiased when the price is trending. **When
a coin is in a sustained run, this is the volatility figure to trust** — the
other range estimators will read high because they mistake direction for noise.

### EWMA

Exponentially weighted, λ = 0.94 (the RiskMetrics daily convention). The newest
bar carries weight (1−λ) and each older bar λ times the one after it, so the
estimate reacts to a regime change within days instead of waiting for a fixed
window to roll over.

Compare EWMA against realised 30d: **EWMA well above the 30-day figure means
volatility is rising right now**, and the calm part of the window is still
holding the average down.

---

## Risk and drawdown

### Max drawdown

The deepest peak-to-trough fall within the window, as a negative fraction. Also
reported: the date of the trough, and the date the price first closed back at
the pre-drawdown peak — `NOT YET` if it never has.

This is the number that describes what holding the asset actually felt like.
An asset can have a fine annual return and still have spent a year 60% down.

### Current drawdown

How far below the window's running high the price sits today. The meter in the
UI shows this as a fraction of the max drawdown: 0 means at the high, 1 means
as bad as it has ever been.

### Sharpe

Annualised excess return per unit of total volatility. Above 1 is strong;
below 0 simply means the asset lost money over the window. The risk-free rate
defaults to 0, the usual convention for crypto.

Sharpe's weakness: it treats upside volatility as risk. An asset that jumps
20% in a day is punished exactly as hard as one that falls 20%.

### Sortino

Sharpe, but only moves below the target count as risk. The downside deviation
is measured against the full sample size, not just the losing bars, which is
what makes it comparable to Sharpe rather than systematically larger.

**Sortino much higher than Sharpe means the volatility was mostly upward** —
the asset was jumpy in the direction you wanted.

### Calmar

Annualised return divided by the absolute max drawdown: return earned per unit
of worst-case pain. Less sensitive to the choice of window than Sharpe, and it
speaks directly to whether you could have held the position.

---

## Tail risk

Crypto returns have far fatter tails than a normal distribution, so both
measures below are **historical** — read straight off the empirical
distribution — rather than parametric. A normal-assumption VaR understates
crypto's bad days badly.

### VaR (Value at Risk)

VaR 95% is the loss that the worst 1 bar in 20 met or exceeded. VaR 99% is the
worst 1 in 100. Returned as a negative fraction.

VaR says *where* the tail starts. It says nothing about how far it extends —
which is exactly the criticism that produced the next measure.

### CVaR (expected shortfall)

The average loss **given** that VaR was breached. If VaR 95% is −4% and CVaR
95% is −7%, then on a bad day you lose at least 4%, but on a typical bad day
you lose 7%.

CVaR is always at least as severe as VaR at the same confidence; the test suite
asserts it.

---

## Distribution shape

### Skew

Asymmetry of the return distribution. **Negative skew means the outsized moves
tend to be crashes** — the asset grinds up and falls fast. Positive skew is the
opposite: frequent small losses punctuated by large gains.

### Excess kurtosis

Tail weight relative to a normal distribution, where 0 is normal. Crypto
routinely reads 3–8, meaning extreme days are several times more common than a
bell curve predicts. A high number is a warning that any model assuming
normality — including a parametric VaR — will be wrong in the direction that
hurts.

### Up bars

Share of bars that closed higher than the previous one. Compare against total
return: a coin that rose overall on fewer than half its bars made its money in
a handful of large jumps, which is a very different risk profile from one that
ground steadily upward.

---

## Indicators

| Indicator | Notes |
| --------- | ----- |
| **RSI 14** | Wilder-smoothed momentum, 0–100. Above 70 conventionally overbought, below 30 oversold. Uses α = 1/14, not a plain EMA — a plain EMA reads noticeably hotter and would not match other terminals. |
| **ATR 14** | Average true range in price units: how far a typical bar travels, including gaps. |
| **ATR %** | The same as a share of price, so it compares across coins of any price. |
| **SMA 20 / 50 / 200** | Simple moving averages. The 200 is the long-term trend line most desks watch. |
| **Bollinger width** | Band width relative to the mid. Narrow bands often precede a large move in either direction — it measures compression, not direction. |
| **Position in range** | Where the last price sits between the window's low and high, 0 to 1, over 30 days and over a year. |

---

## Reading them together

No single number decides anything. A few combinations that carry more
information than their parts:

- **EWMA ≫ realised 30d** — volatility is expanding now.
- **Rogers-Satchell ≪ Parkinson** — the move is trending, not thrashing; the
  gap between them is the trend, which Parkinson misreads as noise.
- **Sortino ≫ Sharpe** — the swings were upward.
- **CVaR far below VaR, high kurtosis** — the tail is long. Position sizing
  based on typical volatility will be wrong on the day it matters.
- **Deep current drawdown, `RECOVERED: NOT YET`** — the window's high is not a
  level this asset has proved it can reclaim.
