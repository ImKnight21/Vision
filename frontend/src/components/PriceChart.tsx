import {
  CandlestickSeries,
  createChart,
  HistogramSeries,
  LineSeries,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type LineData,
  type Time,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useRef } from "react";
import type { Candle } from "../api/types";
import "./PriceChart.css";

interface Props {
  candles: Candle[];
  /** Re-read the palette when the tube changes. */
  phosphor: string;
  showVolume: boolean;
  showMovingAverages: boolean;
}

/** Read a design token so the chart matches the rest of the terminal. */
function token(name: string, fallback: string): string {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

/** Simple moving average over the closes, aligned to the same timestamps. */
function movingAverage(candles: Candle[], window: number): LineData<Time>[] {
  const out: LineData<Time>[] = [];
  let sum = 0;
  const buffer: number[] = [];

  for (const candle of candles) {
    if (candle.close == null) continue;
    buffer.push(candle.close);
    sum += candle.close;
    if (buffer.length > window) sum -= buffer.shift()!;
    if (buffer.length === window) {
      out.push({ time: candle.time as UTCTimestamp, value: sum / window });
    }
  }
  return out;
}

export function PriceChart({ candles, phosphor, showVolume, showMovingAverages }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

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
        scaleMargins: { top: 0.08, bottom: showVolume ? 0.24 : 0.08 },
      },
      timeScale: {
        borderColor: rule,
        timeVisible: true,
        secondsVisible: false,
      },
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

    const bars = candles.filter(
      (c): c is Candle & { open: number; high: number; low: number; close: number } =>
        c.open != null && c.high != null && c.low != null && c.close != null,
    );

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
      volumeSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      });
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

    chart.timeScale().fitContent();

    return () => {
      chart.remove();
      chartRef.current = null;
    };
  }, [candles, phosphor, showVolume, showMovingAverages]);

  return (
    <div className="chart">
      <div className="chart__canvas" ref={containerRef} role="img" aria-label="Price chart" />
      {candles.length === 0 && <p className="chart__empty">NO SIGNAL</p>}
    </div>
  );
}
