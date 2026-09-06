import { useMemo, useState } from "react";
import { api } from "../api/client";
import type { MarketRow } from "../api/types";
import { useAsync } from "../hooks/useAsync";
import { useI18n } from "../i18n/useI18n";
import { magnitude, percent, ratio, signClass } from "../lib/format";
import "./ComparePanel.css";

interface Props {
  /** The coin currently open in the detail view; always part of the comparison. */
  symbol: string;
  interval: string;
  bars: number;
  markets: MarketRow[];
}

const BENCHMARK = "BTCUSDT";
const MAX_SYMBOLS = 8;

/** Colour a correlation cell: strong positive glows, negative reads as danger. */
function cellStyle(value: number | null): React.CSSProperties {
  if (value == null) return {};
  // Crypto correlations cluster between 0.7 and 1.0, so a linear ramp makes
  // every cell look identical. Stretching 0.3..1.0 across the full intensity
  // range is what makes the differences that matter actually visible.
  const absolute = Math.min(Math.abs(value), 1);
  const strength = Math.max(0, (absolute - 0.3) / 0.7);
  const hue = value >= 0 ? "var(--phosphor)" : "var(--down)";
  // color-mix keeps the cell on the tube's own palette, so the heatmap follows
  // the green/amber switch without a second set of colours.
  return { background: `color-mix(in srgb, ${hue} ${(strength * 42).toFixed(1)}%, transparent)` };
}

export function ComparePanel({ symbol, interval, bars, markets }: Props) {
  const { t } = useI18n();
  const [extra, setExtra] = useState<string[]>(["ETHUSDT", "SOLUSDT"]);

  const symbols = useMemo(() => {
    const wanted = [BENCHMARK, symbol, ...extra];
    return [...new Set(wanted)].slice(0, MAX_SYMBOLS);
  }, [symbol, extra]);

  const comparison = useAsync(
    (signal) => api.compare(symbols, interval, bars, signal),
    [symbols.join(","), interval, bars],
    { keepPrevious: true },
  );

  const candidates = useMemo(
    () => markets.filter((row) => !symbols.includes(row.symbol)).slice(0, 60),
    [markets, symbols],
  );

  const data = comparison.data;

  return (
    <section className="compare panel panel--bracketed">
      <div className="panel__title">
        <span>{t("panel.compare")}</span>
        {data && (
          <span className="compare__note">
            {data.bars} {t("compare.subtitle")}
          </span>
        )}
      </div>

      <div className="compare__chips">
        {symbols.map((item) => (
          <span key={item} className="compare__chip">
            {item.replace("USDT", "")}
            {/* The open coin and the benchmark anchor the comparison, so they
                are the two that cannot be removed. */}
            {item !== symbol && item !== BENCHMARK && (
              <button
                type="button"
                className="compare__remove"
                onClick={() => setExtra((list) => list.filter((s) => s !== item))}
                aria-label={`${t("compare.remove")} ${item}`}
              >
                x
              </button>
            )}
          </span>
        ))}

        {symbols.length < MAX_SYMBOLS && candidates.length > 0 && (
          <select
            className="compare__add"
            value=""
            onChange={(event) => {
              const next = event.target.value;
              if (next) setExtra((list) => [...list, next]);
            }}
            aria-label={t("compare.add")}
          >
            <option value="">+ {t("compare.add")}</option>
            {candidates.map((row) => (
              <option key={row.symbol} value={row.symbol}>
                {row.base} - {row.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {comparison.error && (
        <p className="compare__message" role="alert">
          {comparison.error.message}
        </p>
      )}

      {data && data.failed.length > 0 && (
        <p className="compare__message">
          {t("compare.failed")}: {data.failed.join(", ")}
        </p>
      )}

      {data?.matrix && (
        <div className="compare__scroll">
          <table className="compare__matrix" title={t("compare.matrixHint")}>
            <caption className="visually-hidden">{t("compare.matrixHint")}</caption>
            <thead>
              <tr>
                <th scope="col" />
                {data.symbols.map((item) => (
                  <th key={item} scope="col">
                    {item.replace("USDT", "")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.matrix.map((row, rowIndex) => (
                <tr key={data.symbols[rowIndex]}>
                  <th scope="row">{data.symbols[rowIndex]?.replace("USDT", "")}</th>
                  {row.map((value, columnIndex) => (
                    <td
                      key={`${rowIndex}-${columnIndex}`}
                      style={cellStyle(value)}
                      className={rowIndex === columnIndex ? "compare__diagonal" : ""}
                    >
                      {value == null ? "--" : value.toFixed(2)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && (
        <div className="compare__scroll">
          <table className="compare__table">
            <thead>
              <tr>
                <th scope="col">{t("compare.symbol")}</th>
                <th scope="col">{t("compare.totalReturn")}</th>
                <th scope="col">{t("compare.volatility")}</th>
                <th scope="col">{t("compare.sharpe")}</th>
                <th scope="col">{t("compare.maxDrawdown")}</th>
                <th scope="col">{t("compare.beta")}</th>
                <th scope="col">{t("compare.correlation")}</th>
                <th scope="col">{t("compare.hurst")}</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <tr key={row.symbol} className={row.symbol === symbol ? "compare__current" : ""}>
                  <th scope="row">{row.symbol.replace("USDT", "")}</th>
                  <td className={signClass(row.total_return)}>{percent(row.total_return)}</td>
                  <td>{magnitude(row.volatility_30d)}</td>
                  <td className={signClass(row.sharpe)}>{ratio(row.sharpe)}</td>
                  <td className="value-down">{percent(row.max_drawdown)}</td>
                  <td>{ratio(row.beta)}</td>
                  <td>{ratio(row.correlation)}</td>
                  <td>{ratio(row.hurst)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
