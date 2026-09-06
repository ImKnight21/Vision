import type { Stats } from "../api/types";
import { useI18n, type Translate } from "../i18n/useI18n";
import { compact, magnitude, percent, price, ratio, shortDate, signClass } from "../lib/format";
import { Meter } from "./Meter";
import { StatPanel, type StatItem } from "./StatPanel";
import "./StatsPanels.css";

interface Props {
  stats: Stats;
}

/** Durations arrive in days; render them as "353d" / "353д". */
function days(value: number | null, t: Translate): string {
  return value == null ? "--" : `${Math.round(value)}${t("common.days")}`;
}

export function StatsPanels({ stats }: Props) {
  const { t } = useI18n();
  const {
    volatility: vol,
    risk,
    distribution: dist,
    indicators: ind,
    regime,
    liquidity: liq,
    relative,
    returns,
  } = stats;

  const volatilityItems: StatItem[] = [
    { label: t("vol.realized7d"), value: magnitude(vol.realized["7d"]), hint: t("vol.realized7dHint") },
    { label: t("vol.realized30d"), value: magnitude(vol.realized["30d"]), hint: t("vol.realized30dHint") },
    { label: t("vol.realized90d"), value: magnitude(vol.realized["90d"]), hint: t("vol.realized90dHint") },
    { label: t("vol.realizedAll"), value: magnitude(vol.realized.all), hint: t("vol.realizedAllHint") },
    { label: t("vol.ewma"), value: magnitude(vol.ewma), hint: t("vol.ewmaHint") },
    { label: t("vol.parkinson"), value: magnitude(vol.parkinson["30d"]), hint: t("vol.parkinsonHint") },
    { label: t("vol.garmanKlass"), value: magnitude(vol.garman_klass["30d"]), hint: t("vol.garmanKlassHint") },
    { label: t("vol.rogersSatchell"), value: magnitude(vol.rogers_satchell["30d"]), hint: t("vol.rogersSatchellHint") },
  ];

  const regimeItems: StatItem[] = [
    { label: t("regime.hurst"), value: ratio(regime.hurst), hint: t("regime.hurstHint") },
    {
      label: t("regime.autocorrelation"),
      value: ratio(regime.autocorrelation, 3),
      tone: signClass(regime.autocorrelation),
      hint: t("regime.autocorrelationHint"),
    },
    { label: t("regime.volPercentile"), value: magnitude(regime.vol_percentile, 0), hint: t("regime.volPercentileHint") },
    { label: t("regime.volOfVol"), value: ratio(regime.vol_of_vol), hint: t("regime.volOfVolHint") },
    { label: t("regime.trendStrength"), value: ratio(regime.trend_strength), hint: t("regime.trendStrengthHint") },
    {
      label: t("regime.trendChange"),
      value: percent(regime.trend_change),
      tone: signClass(regime.trend_change),
      hint: t("regime.trendChangeHint"),
    },
  ];

  const riskItems: StatItem[] = [
    { label: t("risk.sharpe"), value: ratio(risk.sharpe), tone: signClass(risk.sharpe), hint: t("risk.sharpeHint") },
    { label: t("risk.sortino"), value: ratio(risk.sortino), tone: signClass(risk.sortino), hint: t("risk.sortinoHint") },
    { label: t("risk.calmar"), value: ratio(risk.calmar), tone: signClass(risk.calmar), hint: t("risk.calmarHint") },
    { label: t("risk.maxDrawdown"), value: percent(risk.max_drawdown), tone: signClass(risk.max_drawdown), hint: t("risk.maxDrawdownHint") },
    { label: t("risk.currentDrawdown"), value: percent(risk.current_drawdown), tone: signClass(risk.current_drawdown), hint: t("risk.currentDrawdownHint") },
    { label: t("risk.ulcer"), value: magnitude(risk.ulcer_index), hint: t("risk.ulcerHint") },
    { label: t("risk.underwaterShare"), value: magnitude(risk.underwater_share, 0), hint: t("risk.underwaterShareHint") },
    { label: t("risk.underwaterLongest"), value: days(risk.underwater_longest_days, t), hint: t("risk.underwaterLongestHint") },
    { label: t("risk.recoveryFactor"), value: ratio(risk.recovery_factor), tone: signClass(risk.recovery_factor), hint: t("risk.recoveryFactorHint") },
    { label: t("risk.trough"), value: shortDate(risk.drawdown_trough_at), hint: t("risk.troughHint") },
    {
      label: t("risk.recovered"),
      value: risk.drawdown_recovered_at ? shortDate(risk.drawdown_recovered_at) : t("risk.notYet"),
      tone: risk.drawdown_recovered_at ? "" : "value-down",
      hint: t("risk.recoveredHint"),
    },
  ];

  const tailItems: StatItem[] = [
    { label: t("tail.var95"), value: percent(risk.var_95), tone: "value-down", hint: t("tail.var95Hint") },
    { label: t("tail.cvar95"), value: percent(risk.cvar_95), tone: "value-down", hint: t("tail.cvar95Hint") },
    { label: t("tail.var99"), value: percent(risk.var_99), tone: "value-down", hint: t("tail.var99Hint") },
    { label: t("tail.cvar99"), value: percent(risk.cvar_99), tone: "value-down", hint: t("tail.cvar99Hint") },
    { label: t("tail.worst"), value: percent(dist.worst), tone: "value-down", hint: t("tail.worstHint") },
    { label: t("tail.best"), value: percent(dist.best), tone: "value-up", hint: t("tail.bestHint") },
    { label: t("tail.ratio"), value: ratio(risk.tail_ratio), hint: t("tail.ratioHint") },
    { label: t("tail.omega"), value: ratio(risk.omega), hint: t("tail.omegaHint") },
  ];

  const shapeItems: StatItem[] = [
    { label: t("dist.skew"), value: ratio(dist.skew), tone: signClass(dist.skew), hint: t("dist.skewHint") },
    { label: t("dist.kurtosis"), value: ratio(dist.kurtosis), hint: t("dist.kurtosisHint") },
    { label: t("dist.upBars"), value: magnitude(dist.positive_share), hint: t("dist.upBarsHint") },
    { label: t("dist.gainToPain"), value: ratio(risk.gain_to_pain), tone: signClass(risk.gain_to_pain), hint: t("dist.gainToPainHint") },
    { label: t("dist.totalReturn"), value: percent(returns.total), tone: signClass(returns.total), hint: t("dist.totalReturnHint") },
    { label: t("dist.cagr"), value: percent(returns.cagr), tone: signClass(returns.cagr), hint: t("dist.cagrHint") },
  ];

  const relativeItems: StatItem[] = relative
    ? [
        { label: t("rel.correlation"), value: ratio(relative.correlation), hint: t("rel.correlationHint") },
        { label: t("rel.beta"), value: ratio(relative.beta), hint: t("rel.betaHint") },
        { label: t("rel.alpha"), value: percent(relative.alpha), tone: signClass(relative.alpha), hint: t("rel.alphaHint") },
        { label: t("rel.rSquared"), value: ratio(relative.r_squared), hint: t("rel.rSquaredHint") },
        { label: t("rel.upCapture"), value: ratio(relative.up_capture), hint: t("rel.upCaptureHint") },
        { label: t("rel.downCapture"), value: ratio(relative.down_capture), hint: t("rel.downCaptureHint") },
        { label: t("rel.trackingError"), value: magnitude(relative.tracking_error), hint: t("rel.trackingErrorHint") },
        {
          label: t("rel.relativeReturn"),
          value: percent(relative.relative_return),
          tone: signClass(relative.relative_return),
          hint: t("rel.relativeReturnHint"),
        },
      ]
    : [];

  const liquidityItems: StatItem[] = [
    { label: t("liq.impact"), value: magnitude(liq.amihud, 3), hint: t("liq.impactHint") },
    { label: t("liq.volumeZ"), value: ratio(liq.volume_zscore), tone: signClass(liq.volume_zscore), hint: t("liq.volumeZHint") },
    { label: t("liq.volumeTrend"), value: ratio(liq.volume_trend), hint: t("liq.volumeTrendHint") },
    {
      label: t("liq.medianVolume"),
      value: liq.dollar_volume_median == null ? "--" : `$${compact(liq.dollar_volume_median)}`,
      hint: t("liq.medianVolumeHint"),
    },
    {
      label: t("liq.minVolume"),
      value: liq.dollar_volume_min == null ? "--" : `$${compact(liq.dollar_volume_min)}`,
      hint: t("liq.minVolumeHint"),
    },
  ];

  const indicatorItems: StatItem[] = [
    { label: t("ind.rsi"), value: ratio(ind.rsi_14, 1), hint: t("ind.rsiHint") },
    { label: t("ind.atr"), value: price(ind.atr_14), hint: t("ind.atrHint") },
    { label: t("ind.atrPercent"), value: magnitude(ind.atr_percent_14, 2), hint: t("ind.atrPercentHint") },
    { label: t("ind.sma20"), value: price(ind.sma_20) },
    { label: t("ind.sma50"), value: price(ind.sma_50) },
    { label: t("ind.sma200"), value: price(ind.sma_200), hint: t("ind.sma200Hint") },
    { label: t("ind.bbWidth"), value: magnitude(ind.bollinger_width, 1), hint: t("ind.bbWidthHint") },
  ];

  // The drawdown meter reads 0 at the window high and 1 at its worst point, so
  // it answers "how close to the worst this has ever been" at a glance.
  const drawdownDepth =
    risk.current_drawdown != null && risk.max_drawdown
      ? risk.current_drawdown / risk.max_drawdown
      : null;

  // Hurst runs roughly 0.2 to 0.8 in practice; stretching that span across the
  // track makes the difference between 0.45 and 0.6 actually visible.
  const hurstPosition =
    regime.hurst == null ? null : (regime.hurst - 0.2) / 0.6;

  return (
    <div className="stats-grid">
      <StatPanel title={t("panel.volatility")} note={t("panel.volatilityNote")} items={volatilityItems} />

      <StatPanel title={t("panel.regime")} items={regimeItems}>
        <Meter
          label={t("regime.meter")}
          position={hurstPosition}
          leftLabel={t("regime.reverting")}
          rightLabel={t("regime.trending")}
          marks={[(0.5 - 0.2) / 0.6]}
          hint={t("regime.hurstHint")}
        />
      </StatPanel>

      <StatPanel title={t("panel.risk")} items={riskItems}>
        <Meter
          label={t("risk.drawdownMeter")}
          position={drawdownDepth}
          leftLabel={t("risk.atHigh")}
          rightLabel={t("risk.atWorst")}
          hint={t("risk.drawdownMeterHint")}
        />
      </StatPanel>

      <StatPanel title={t("panel.tail")} note={t("panel.tailNote")} items={tailItems} />

      <StatPanel title={t("panel.distribution")} items={shapeItems} />

      <StatPanel
        title={t("panel.relative")}
        note={relative?.benchmark}
        items={relativeItems}
      >
        {!relative && <p className="stats-grid__note">{t("rel.isBenchmark")}</p>}
      </StatPanel>

      <StatPanel title={t("panel.liquidity")} items={liquidityItems} />

      <StatPanel title={t("panel.indicators")} items={indicatorItems}>
        <Meter
          label={t("ind.rsi")}
          position={ind.rsi_14 == null ? null : ind.rsi_14 / 100}
          leftLabel={t("ind.oversold")}
          rightLabel={t("ind.overbought")}
          marks={[0.3, 0.7]}
          hint={t("ind.rsiHint")}
        />
        <Meter
          label={t("ind.range30d")}
          position={stats.price.range_30d.position}
          leftLabel={price(stats.price.range_30d.low)}
          rightLabel={price(stats.price.range_30d.high)}
          hint={t("ind.range30dHint")}
        />
        <Meter
          label={t("ind.range365d")}
          position={stats.price.range_365d.position}
          leftLabel={price(stats.price.range_365d.low)}
          rightLabel={price(stats.price.range_365d.high)}
          hint={t("ind.range365dHint")}
        />
      </StatPanel>
    </div>
  );
}
