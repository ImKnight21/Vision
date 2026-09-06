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
- **Hurst above 0.5 with high trend strength** — a real, orderly trend, so
  continuation is the base case rather than the hopeful one.
- **Volatility percentile above 90 with high vol-of-vol** — the asset is at the
  top of its own range *and* prone to regime switches. Whatever size the current
  volatility justifies, it will not justify it for long.
- **Beta above 1 with down-capture above up-capture** — the coin takes more of
  BTC's falls than of its rises. That combination is what a negative alpha looks
  like before it shows up in the alpha figure.
- **Rising price, volume trend below 1, volume z-score negative** — the move is
  running on fewer participants each bar.
- **High tail ratio with negative skew** — rare large gains inside a
  distribution that still loses more often than it wins. Both facts are true and
  neither alone describes it.

---

## Regime: does it trend or revert?

Volatility says how far price moves. These say whether the moves tend to
continue or be given back, which decides whether a breakout or a fade is the
sensible read.

### Hurst exponent

Estimated by rescaled-range (R/S) analysis over log-spaced windows, fitted as a
slope in log-log space.

- **0.5** is a random walk.
- **Above 0.5** the series is persistent: moves follow through, so breakouts
  are worth more and mean-reversion trades are fighting the tape.
- **Below 0.5** it is anti-persistent: moves get given back, so fades work and
  breakouts fail more often than a coin flip.

Crypto majors on daily bars usually sit just above 0.5. Needs at least 128
bars; below that it returns null rather than a number built from noise.

### Autocorrelation (lag 1)

Correlation of each bar's return with the previous one. Positive means
momentum, negative means reversal. The magnitude is almost always small; **the
sign is the signal**, not the size.

### Volatility percentile

Where the current 30-bar volatility sits inside the distribution of this
asset's own past 30-bar volatilities, 0 to 1.

This is the context an absolute figure cannot give. "60% annualised" means
nothing alone. 60% at the 95th percentile means the asset is about as agitated
as it has ever been; 60% at the 20th means this is a quiet spell for it.

### Volatility of volatility

Coefficient of variation of the rolling volatility series. High values mean the
asset switches between calm and violent regimes rather than holding one level,
so any single volatility number has a short shelf life and position sizing off
it will be stale quickly.

### Trend strength and trend change

`trend_strength` is the R-squared of a straight line fitted through log price
over the last 50 bars: how *orderly* the move is, not which way it went. High
means a clean directional run; low means chop that happened to drift.

`trend_change` is how far that fitted line travelled across the window, as a
fraction. It is deliberately **not annualised**: compounding a 50-bar drift out
to a year produces figures like +1300% that are arithmetically correct and
analytically worthless.

Read them together. A large `trend_change` with a low `trend_strength` is not a
trend, it is noise with a slope.

---

## Duration: how long, not just how deep

Max drawdown reports the worst moment. These report what the whole experience
was like, which is what determines whether a position was actually holdable.

| Measure | Reads as |
| ------- | -------- |
| **Ulcer index** | Root-mean-square drawdown. Depth and duration in one number: a long shallow slump and a brief violent crash stop looking alike. |
| **Time under water** | Share of bars spent below a previous high. An asset can post a fine annual return and have been underwater 95% of the time. |
| **Longest slump** | The longest unbroken stretch below a previous high, in days. |
| **Recovery factor** | Window return divided by the depth of the worst drawdown. Like Calmar but using the raw window return, so a short sample does not distort it. |

---

## Payoff asymmetry

Skew hints at asymmetry; these state it in units you can act on.

- **Tail ratio** - the 95th percentile gain over the absolute 5th percentile
  loss. Above 1 means the good outliers were bigger than the bad ones.
- **Omega** - total gains above zero divided by total losses below it. It uses
  the entire distribution rather than its first two moments, so unlike Sharpe
  it makes no normality assumption. For crypto that matters.
- **Gain to pain** - the sum of all returns over the sum of the losing ones. A
  blunt read on whether the winners paid for the losers.

---

## Liquidity

Volatility describes the price you see; liquidity describes whether you could
have traded at it. For a large cap the distinction rarely bites. For a thin alt
it is often the whole risk, and a returns-only view misses it entirely.

- **Impact per $1M** (Amihud) - the fractional price move caused by a million
  dollars of volume. `0.0001` means $1M shifts the price about 0.01%. Higher
  means thinner. Compare it across coins, never against an absolute threshold.
- **Volume z-score** - how unusual the latest bar's turnover is, in standard
  deviations. Above 2 is a spike, which corroborates a price move. **A breakout
  on below-average volume is the one to distrust.**
- **Volume trend** - recent turnover over its longer-run average. Sustained
  readings below 1 during a price rise mean the move is running on fewer and
  fewer participants.
- **Median and thinnest-day volume** - the median describes an ordinary day (a
  mean would let one listing-day spike speak for the month); the minimum is the
  liquidity you can actually rely on.

---

## Relative to Bitcoin

Most alts are, statistically, leveraged bets on BTC with extra noise. These
separate the part of a move that was simply the market from the part that
belonged to the coin, which is the difference between "it went up" and "it
outperformed". All are computed over the bars the two series **share**, so a
short history shortens the comparison rather than misaligning it.

| Measure | Reads as |
| ------- | -------- |
| **Correlation** | How closely the coin moves with BTC. Near 1 means it offers almost no diversification. |
| **Beta** | Move per 1% move in BTC. Above 1 amplifies the market in both directions. |
| **Alpha** | Jensen's alpha, annualised: the return left over once the BTC exposure beta describes has been paid for. Negative means the coin did not earn the risk it carried. |
| **R-squared** | Share of the coin's movement explained by BTC. High means it is essentially a leveraged BTC position wearing a different ticker. |
| **Up / down capture** | Share of BTC's move captured on its up and down bars. Up above 1 with down below 1 is the rare good shape. Both far above 1 is simply leverage. |
| **Tracking error** | How far the coin's path strays from BTC's, annualised. |

The comparison view extends this to a **correlation matrix** across up to eight
coins. Correlations there are computed over the bars every symbol shares, so
adding a young coin shortens the window for the whole matrix. The `bars` count
in the panel header says how many that is.

---

## Considered and left out

Deliberate omissions, so the absence reads as a decision rather than an
oversight:

- **GARCH / stochastic volatility models.** Better volatility forecasts, but
  they need fitting, tuning and a story about model risk. EWMA plus the
  volatility percentile answers "is volatility rising, and is it high for this
  coin" without any of that.
- **Parametric VaR.** Cheaper than the historical version, and wrong in exactly
  the direction that hurts: crypto's excess kurtosis of 3 to 8 makes the normal
  assumption fail precisely on the days it matters.
- **Order-book depth and spread.** The truest liquidity measures, but they need
  a live book feed and cannot be reconstructed from candles. Amihud is the
  honest approximation available from OHLCV.
- **On-chain metrics** (active addresses, exchange flows, MVRV). Genuinely
  informative and completely outside what a price feed can supply. They would
  need a second data provider and a second set of caveats.
- **Backtested strategy returns.** The project charts what happened; simulating
  what a rule would have earned invites overfitting and would turn an
  informational tool into an implied recommendation.
