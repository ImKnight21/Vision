import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api/client";
import { CoinHeader } from "./components/CoinHeader";
import { ComparePanel } from "./components/ComparePanel";
import { Header } from "./components/Header";
import { IntervalPicker } from "./components/IntervalPicker";
import { MarketList } from "./components/MarketList";
import { PriceChart } from "./components/PriceChart";
import { StatsPanels } from "./components/StatsPanels";
import { useAsync } from "./hooks/useAsync";
import { useCrtEffects, useLocale, usePhosphor } from "./hooks/useDisplay";
import { I18nContext, translator } from "./i18n/useI18n";
import "./App.css";

/** Intervals worth offering for a statistics view. Sub-hourly bars make the
 *  annualised numbers jumpy without telling you much more. */
const INTERVALS = ["15m", "1h", "4h", "12h", "1d", "3d", "1w"];

const DEFAULT_SYMBOL = "BTCUSDT";

export function App() {
  const [phosphor, togglePhosphor] = usePhosphor();
  const [fx, toggleFx] = useCrtEffects();
  const [locale, toggleLocale] = useLocale();
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [interval, setInterval] = useState("1d");
  const [bars, setBars] = useState(500);
  const [showVolume, setShowVolume] = useState(true);
  const [showMovingAverages, setShowMovingAverages] = useState(true);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [compareOpen, setCompareOpen] = useState(false);

  // Rebuilding `t` only when the language changes keeps every consumer from
  // re-rendering on unrelated state.
  const i18n = useMemo(
    () => ({ locale, t: translator(locale), toggleLocale }),
    [locale, toggleLocale],
  );

  const markets = useAsync((signal) => api.markets(150, signal), []);

  // `keepPrevious` leaves the last coin on screen while the next one loads, so
  // switching symbols does not blank the whole page.
  const overview = useAsync(
    (signal) => api.overview(symbol, interval, bars, signal),
    [symbol, interval, bars],
    { keepPrevious: true },
  );

  const selectedMarket = useMemo(
    () => markets.data?.markets.find((row) => row.symbol === symbol),
    [markets.data, symbol],
  );

  const selectSymbol = useCallback((next: string) => {
    setSymbol(next);
    setDrawerOpen(false);
  }, []);

  // Escape closes the mobile drawer, the way a dialog is expected to behave.
  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setDrawerOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerOpen]);

  const status = overview.error || markets.error
    ? "error"
    : overview.loading || markets.loading
      ? "loading"
      : "live";

  const list = (
    <MarketList
      markets={markets.data?.markets ?? []}
      selected={symbol}
      onSelect={selectSymbol}
      loading={markets.loading}
    />
  );

  return (
    <I18nContext.Provider value={i18n}>
      <div className="app">
        <Header
          phosphor={phosphor}
          onTogglePhosphor={togglePhosphor}
          fx={fx}
          onToggleFx={toggleFx}
          onOpenMarkets={() => setDrawerOpen(true)}
          onOpenCompare={() => setCompareOpen((open) => !open)}
          compareOpen={compareOpen}
          status={status}
        />

        {(overview.slow || markets.slow) && (
        <p className="app__waking" role="status">
          <span className="app__waking-spinner" aria-hidden="true" />
          <strong>{i18n.t("status.waking")}</strong>
          <span className="app__waking-hint">{i18n.t("status.wakingHint")}</span>
        </p>
      )}

      <div className="app__body">
          <aside className="app__sidebar">{list}</aside>

          <main className="app__main">
            <CoinHeader
              symbol={symbol}
              market={selectedMarket}
              stats={overview.data?.stats ?? null}
            />

            <IntervalPicker
              intervals={INTERVALS}
              value={interval}
              onChange={setInterval}
              bars={bars}
              onBarsChange={setBars}
              showVolume={showVolume}
              onShowVolumeChange={setShowVolume}
              showMovingAverages={showMovingAverages}
              onShowMovingAveragesChange={setShowMovingAverages}
            />

            <section className="app__chart panel panel--bracketed">
              <div className="panel__title">
                <span>
                  {symbol} · {interval.toUpperCase()}
                </span>
                <span className="app__chart-source">
                  {(overview.data?.source ?? "").toUpperCase()}
                </span>
              </div>
              <PriceChart
                candles={overview.data?.candles ?? []}
                phosphor={`${phosphor}-${fx}`}
                showVolume={showVolume}
                showMovingAverages={showMovingAverages}
              />
            </section>

            {overview.error && (
              <p className="app__error panel" role="alert">
                <span className="app__error-tag">{i18n.t("common.error")}</span>
                {overview.error.message}
                <button type="button" className="app__retry" onClick={overview.reload}>
                  {i18n.t("common.retry")}
                </button>
              </p>
            )}

            {compareOpen && (
              <ComparePanel
                symbol={symbol}
                interval={interval}
                bars={bars}
                markets={markets.data?.markets ?? []}
              />
            )}

            {overview.data && <StatsPanels stats={overview.data.stats} />}

            <p className="app__disclaimer">{i18n.t("disclaimer")}</p>
          </main>
        </div>

        {drawerOpen && (
          <div
            className="app__drawer"
            role="dialog"
            aria-modal="true"
            aria-label={i18n.t("markets.title")}
          >
            <button
              type="button"
              className="app__scrim"
              onClick={() => setDrawerOpen(false)}
              aria-label={i18n.t("markets.title")}
            />
            <div className="app__drawer-panel">{list}</div>
          </div>
        )}
      </div>
    </I18nContext.Provider>
  );
}
