import type { Stats } from "../api/types";
import { magnitude, percent, price, ratio, shortDate, signClass } from "../lib/format";
import { Meter } from "./Meter";
import { StatPanel, type StatItem } from "./StatPanel";
import "./StatsPanels.css";

interface Props {
  stats: Stats;
}

export function StatsPanels({ stats }: Props) {
  const { volatility: vol, risk, distribution: dist, indicators: ind, returns } = stats;

  const volatilityItems: StatItem[] = [
    {
      label: "Realized 7d",
      value: magnitude(vol.realized["7d"]),
      hint: "Annualised standard deviation of log returns over the last 7 days.",
    },
    {
      label: "Realized 30d",
      value: magnitude(vol.realized["30d"]),
      hint: "The same measure over 30 days — the usual reference window.",
    },
    {
      label: "Realized 90d",
      value: magnitude(vol.realized["90d"]),
      hint: "Over 90 days: slower to react, but far less noisy.",
    },
    {
      label: "Realized all",
      value: magnitude(vol.realized.all),
      hint: "Over the whole loaded history.",
    },
    {
      label: "EWMA",
      value: magnitude(vol.ewma),
      hint: "Exponentially weighted, lambda 0.94. Reacts to a regime change faster than a fixed window.",
    },
    {
      label: "Parkinson 30d",
      value: magnitude(vol.parkinson["30d"]),
      hint: "Uses the high-low range instead of closes: more precise, but blind to gaps between bars.",
    },
    {
      label: "Garman-Klass 30d",
      value: magnitude(vol.garman_klass["30d"]),
      hint: "Uses the full OHLC bar. The most efficient estimator when price is not trending.",
    },
    {
      label: "Rogers-Satchell 30d",
      value: magnitude(vol.rogers_satchell["30d"]),
      hint: "The range estimator that stays unbiased while price trends. Trust this one during a strong run.",
    },
  ];

  const riskItems: StatItem[] = [
    {
      label: "Sharpe",
      value: ratio(risk.sharpe),
      tone: signClass(risk.sharpe),
      hint: "Annualised return per unit of total volatility. Above 1 is strong; below 0 means the asset lost money.",
    },
    {
      label: "Sortino",
      value: ratio(risk.sortino),
      tone: signClass(risk.sortino),
      hint: "Like Sharpe, but only downside moves count as risk. Higher than Sharpe means the swings were mostly upward.",
    },
    {
      label: "Calmar",
      value: ratio(risk.calmar),
      tone: signClass(risk.calmar),
      hint: "Annualised return divided by the worst drawdown: how much you earned per unit of pain.",
    },
    {
      label: "Max drawdown",
      value: percent(risk.max_drawdown),
      tone: signClass(risk.max_drawdown),
      hint: "The deepest peak-to-trough fall inside this window.",
    },
    {
      label: "Current drawdown",
      value: percent(risk.current_drawdown),
      tone: signClass(risk.current_drawdown),
      hint: "How far below the window's high the price sits right now.",
    },
    {
      label: "Trough",
      value: shortDate(risk.drawdown_trough_at),
      hint: "When the deepest point was reached.",
    },
    {
      label: "Recovered",
      value: risk.drawdown_recovered_at ? shortDate(risk.drawdown_recovered_at) : "NOT YET",
      tone: risk.drawdown_recovered_at ? "" : "value-down",
      hint: "When price first closed back at the pre-drawdown peak.",
    },
  ];

  const tailItems: StatItem[] = [
    {
      label: "VaR 95%",
      value: percent(risk.var_95),
      tone: "value-down",
      hint: "On the worst 1 bar in 20, the loss was at least this large.",
    },
    {
      label: "CVaR 95%",
      value: percent(risk.cvar_95),
      tone: "value-down",
      hint: "Average loss across those worst 5% of bars: how bad the bad days actually get.",
    },
    {
      label: "VaR 99%",
      value: percent(risk.var_99),
      tone: "value-down",
      hint: "The same idea for the worst 1 bar in 100.",
    },
    {
      label: "CVaR 99%",
      value: percent(risk.cvar_99),
      tone: "value-down",
      hint: "Average loss inside that extreme 1% tail.",
    },
    {
      label: "Worst bar",
      value: percent(dist.worst),
      tone: "value-down",
      hint: "Largest single-bar loss in the window.",
    },
    {
      label: "Best bar",
      value: percent(dist.best),
      tone: "value-up",
      hint: "Largest single-bar gain in the window.",
    },
  ];

  const shapeItems: StatItem[] = [
    {
      label: "Skew",
      value: ratio(dist.skew),
      tone: signClass(dist.skew),
      hint: "Asymmetry of returns. Negative means the outsized moves tend to be crashes.",
    },
    {
      label: "Excess kurtosis",
      value: ratio(dist.kurtosis),
      hint: "Tail weight versus a normal distribution. Above 0 means outliers are more common than a bell curve predicts.",
    },
    {
      label: "Up bars",
      value: magnitude(dist.positive_share),
      hint: "Share of bars that closed higher than the one before.",
    },
    {
      label: "Total return",
      value: percent(returns.total),
      tone: signClass(returns.total),
      hint: "Change over the entire loaded window.",
    },
    {
      label: "CAGR",
      value: percent(returns.cagr),
      tone: signClass(returns.cagr),
      hint: "That same return expressed as an annual compounding rate.",
    },
  ];

  const indicatorItems: StatItem[] = [
    {
      label: "RSI 14",
      value: ratio(ind.rsi_14, 1),
      hint: "Momentum on a 0-100 scale. Above 70 is conventionally overbought, below 30 oversold.",
    },
    {
      label: "ATR 14",
      value: price(ind.atr_14),
      hint: "Average true range in price units: how far a typical bar travels.",
    },
    {
      label: "ATR %",
      value: magnitude(ind.atr_percent_14, 2),
      hint: "The same range as a share of price, so it can be compared across coins.",
    },
    { label: "SMA 20", value: price(ind.sma_20) },
    { label: "SMA 50", value: price(ind.sma_50) },
    {
      label: "SMA 200",
      value: price(ind.sma_200),
      hint: "The long-term trend line most desks watch.",
    },
    {
      label: "BB width",
      value: magnitude(ind.bollinger_width, 1),
      hint: "Bollinger band width relative to price. Narrow bands often precede a large move.",
    },
  ];

  // The drawdown meter reads 0 at the window high and 1 at its worst point, so
  // it answers "how close to the worst this has ever been" at a glance.
  const drawdownDepth =
    risk.current_drawdown != null && risk.max_drawdown
      ? risk.current_drawdown / risk.max_drawdown
      : null;

  return (
    <div className="stats-grid">
      <StatPanel title="Volatility" note="annualised" items={volatilityItems} />

      <StatPanel title="Risk &amp; Drawdown" items={riskItems}>
        <Meter
          label="Depth of current drawdown"
          position={drawdownDepth}
          leftLabel="AT HIGH"
          rightLabel="AT WORST"
          hint="Where the present drawdown sits between the window's high and its deepest point."
        />
      </StatPanel>

      <StatPanel title="Tail Risk" note="per bar" items={tailItems} />

      <StatPanel title="Distribution" items={shapeItems} />

      <StatPanel title="Indicators" items={indicatorItems}>
        <Meter
          label="RSI 14"
          position={ind.rsi_14 == null ? null : ind.rsi_14 / 100}
          leftLabel="30 OVERSOLD"
          rightLabel="OVERBOUGHT 70"
          marks={[0.3, 0.7]}
          hint="Relative Strength Index over 14 bars."
        />
        <Meter
          label="Position in 30d range"
          position={stats.price.range_30d.position}
          leftLabel={price(stats.price.range_30d.low)}
          rightLabel={price(stats.price.range_30d.high)}
          hint="Where the last price sits between the 30-day low and high."
        />
        <Meter
          label="Position in 1y range"
          position={stats.price.range_365d.position}
          leftLabel={price(stats.price.range_365d.low)}
          rightLabel={price(stats.price.range_365d.high)}
          hint="The same, measured over a year of bars."
        />
      </StatPanel>
    </div>
  );
}
