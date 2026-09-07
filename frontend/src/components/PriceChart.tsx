import {
  CandlestickSeries,
  createChart,
  HistogramSeries,
  LineSeries,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type Time,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Candle } from "../api/types";
import { useI18n } from "../i18n/useI18n";
import { compact, percent, price, signClass } from "../lib/format";
import "./PriceChart.css";

interface Props {
  candles: Candle[];
  /** Re-read the palette when the tube or effects change. */
  phosphor: string;
  showVolume: boolean;
  showMovingAverages: boolean;
  /** Newest bars from the live poll, merged onto the tail of `candles`. */
  live?: Candle[] | null;
  /** True while the poll is actually delivering. */
  streaming?: boolean;
}

/** A bar with every OHLC field present, which is what the chart can draw. */
type SolidCandle = Candle & {
  open: number;
  high: number;
  low: number;
  close: number;
};

function solid(candles: Candle[]): SolidCandle[] {
  return candles.filter(
    (c): c is SolidCandle =>
      c.open != null && c.high != null && c.low != null && c.close != null,
  );
}

/** Read a design token so the chart matches the rest of the terminal. */
function token(name: string, fallback: string): string {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

/** Simple moving average over the closes, aligned to the same timestamps. */
function movingAverage(candles: SolidCandle[], window: number): LineData<Time>[] {
  const out: LineData<Time>[] = [];
  let sum = 0;
  const buffer: number[] = [];

  for (const candle of candles) {
    buffer.push(candle.close);
    sum += candle.close;
    if (buffer.length > window) sum -= buffer.shift()!;
    if (buffer.length === window) {
      out.push({ time: candle.time as UTCTimestamp, value: sum / window });
    }
  }
  return out;
}

export function PriceChart({
  candles,
  phosphor,
  showVolume,
  showMovingAverages,
  live,
  streaming = false,
}: Props) {
  const { t } = useI18n();
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const priceRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  /** Timestamp of the bar under the cursor; null when the cursor is away. */
  const [hoveredTime, setHoveredTime] = useState<number | null>(null);

  const bars = useMemo(() => solid(candles), [candles]);
  const liveBars = useMemo(() => solid(live ?? []), [live]);

  // What the legend reads. The chart itself is not rebuilt for a live bar --
  // that is pushed through `series.update` below -- so this merge exists only
  // so the hover readout and the LIVE row agree with what is drawn.
  const shownBars = useMemo(() => {
    if (!liveBars.length) return bars;
    const cutoff = liveBars[0]!.time;
    return [...bars.filter((c) => c.time < cutoff), ...liveBars];
  }, [bars, liveBars]);

  const byTime = useMemo(
    () => new Map(shownBars.map((c) => [c.time, c])),
    [shownBars],
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const phosphorColor = token("--phosphor", "#4dff85");
    const up = token("--up", "#4dff85");
    const down = token("--down", "#ff7a68");
    const textDim = token("--text-dim", "#8fd6a4");
    const rule = token("--rule", "rgba(77,255,133,0.26)");

    const chart = createChart(container, {
      // Pin the locale: otherwise axis dates follow the viewer's system
      // language and the chart stops matching the rest of the interface.
      localization: { locale: "en-US" },
      layout: {
        background: { color: "transparent" },
        textColor: textDim,
        fontFamily: token("--font-mono", "monospace"),
        fontSize: 11,
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: rule, style: 1 },
        horzLines: { color: rule, style: 1 },
      },
      rightPriceScale: {
        borderColor: rule,
        // Leave room at the bottom for the volume overlay to sit under price.
        scaleMargins: { top: 0.16, bottom: showVolume ? 0.24 : 0.08 },
      },
      timeScale: { borderColor: rule, timeVisible: true, secondsVisible: false },
      crosshair: {
        mode: 0, // free crosshair, the way a terminal cursor moves
        vertLine: { color: phosphorColor, width: 1, style: 3, labelBackgroundColor: phosphorColor },
        horzLine: { color: phosphorColor, width: 1, style: 3, labelBackgroundColor: phosphorColor },
      },
      handleScale: { axisPressedMouseMove: { price: false } },
      autoSize: true,
    });
    chartRef.current = chart;

    const priceSeries = chart.addSeries(CandlestickSeries, {
      upColor: up,
      downColor: down,
      borderUpColor: up,
      borderDownColor: down,
      wickUpColor: up,
      wickDownColor: down,
      priceLineColor: phosphorColor,
      priceLineStyle: 2,
    });
    priceRef.current = priceSeries;

    priceSeries.setData(
      bars.map<CandlestickData<Time>>((c) => ({
        time: c.time as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      })),
    );

    if (showVolume) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: "volume" },
        // An empty price scale id makes this an overlay on its own scale.
        priceScaleId: "",
        priceLineVisible: false,
        lastValueVisible: false,
      });
      volumeRef.current = volumeSeries;
      volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
      volumeSeries.setData(
        bars
          .filter((c) => c.volume != null)
          .map<HistogramData<Time>>((c) => ({
            time: c.time as UTCTimestamp,
            value: c.volume as number,
            // Tint volume by the bar's direction; it reads at a glance.
            color: c.close >= c.open ? `${up}44` : `${down}44`,
          })),
      );
    }

    if (showMovingAverages) {
      for (const [window, opacity] of [
        [50, "cc"],
        [200, "77"],
      ] as const) {
        if (bars.length < window) continue;
        const line = chart.addSeries(LineSeries, {
          color: `${phosphorColor}${opacity}`,
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        });
        line.setData(movingAverage(bars, window));
      }
    }

    // Drive the legend from the crosshair. `param.time` is absent whenever the
    // pointer leaves the plot, which is the signal to fall back to the newest
    // bar rather than freezing on whatever was last hovered.
    chart.subscribeCrosshairMove((param) => {
      setHoveredTime(typeof param.time === "number" ? param.time : null);
    });

    chart.timeScale().fitContent();

    // The legend floats over the plot, and the price axis is drawn across the
    // full height including the strip the legend sits in. Publish the axis
    // width so the legend can stop short of it instead of printing over the
    // price labels, which is what it did on a narrow screen.
    const publishScaleWidth = () => {
      const width = chart.priceScale("right").width();
      // Set on the parent, not the canvas: the legend is the canvas's sibling
      // and would never see a property declared on it.
      container.parentElement?.style.setProperty(
        "--chart-scale-width",
        `${Math.ceil(width)}px`,
      );
    };
    publishScaleWidth();
    const observer = new ResizeObserver(publishScaleWidth);
    observer.observe(container);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      priceRef.current = null;
      volumeRef.current = null;
    };
  }, [bars, phosphor, showVolume, showMovingAverages]);

  // Push the live bar into the existing series. `update` replaces the last bar
  // when the timestamp matches and appends when it is newer, so rebuilding the
  // chart -- and throwing away the viewer's pan and zoom -- is never needed.
  useEffect(() => {
    const series = priceRef.current;
    if (!series || !liveBars.length) return;

    const newest = bars.length ? bars[bars.length - 1]!.time : 0;
    for (const bar of liveBars) {
      // A bar older than the loaded history would be an out-of-order update,
      // which lightweight-charts rejects by throwing.
      if (bar.time < newest) continue;
      series.update({
        time: bar.time as UTCTimestamp,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
      });
      if (volumeRef.current && bar.volume != null) {
        const up = token("--up", "#4dff85");
        const down = token("--down", "#ff7a68");
        volumeRef.current.update({
          time: bar.time as UTCTimestamp,
          value: bar.volume,
          color: bar.close >= bar.open ? `${up}44` : `${down}44`,
        });
      }
    }
  }, [liveBars, bars]);

  const latest = shownBars.length ? shownBars[shownBars.length - 1]! : null;
  const shown = (hoveredTime != null ? byTime.get(hoveredTime) : null) ?? latest;
  // The newest bar of a live feed is still forming, so say so rather than
  // presenting an in-progress close as a settled one.
  const isLive = shown != null && latest != null && shown.time === latest.time;
  const change = shown && shown.open > 0 ? shown.close / shown.open - 1 : null;

  return (
    <div className="chart">
      {shown && (
        <dl className="chart__legend" aria-live="off">
          <Field label={t("chart.open")} value={price(shown.open)} />
          <Field label={t("chart.high")} value={price(shown.high)} />
          <Field label={t("chart.low")} value={price(shown.low)} />
          <Field label={t("chart.close")} value={price(shown.close)} tone={signClass(change)} />
          <Field label={t("chart.change")} value={percent(change)} tone={signClass(change)} />
          {shown.volume != null && (
            <Field
              label={t("chart.volume")}
              value={compact(shown.volume)}
              className="chart__field--volume"
            />
          )}
          {isLive && (
            <dd
              className={`chart__live${streaming ? " chart__live--streaming" : ""}`}
              title={streaming ? t("chart.streamingHint") : t("chart.liveHint")}
            >
              <span className="chart__live-dot" aria-hidden="true" />
              {streaming ? t("chart.streaming") : t("chart.live")}
            </dd>
          )}
        </dl>
      )}

      <div className="chart__canvas" ref={containerRef} role="img" aria-label={t("chart.label")} />
      {candles.length === 0 && <p className="chart__empty">{t("chart.empty")}</p>}
    </div>
  );
}

function Field({
  label,
  value,
  tone,
  className,
}: {
  label: string;
  value: string;
  tone?: string;
  className?: string;
}) {
  return (
    <div className={`chart__field${className ? ` ${className}` : ""}`}>
      <dt className="chart__field-label">{label}</dt>
      <dd className={`chart__field-value ${tone ?? ""}`}>{value}</dd>
    </div>
  );
}
