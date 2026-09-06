import { useDeferredValue, useMemo, useState } from "react";
import type { MarketRow } from "../api/types";
import { useI18n } from "../i18n/useI18n";
import { compact, percent, price, signClass } from "../lib/format";
import "./MarketList.css";

interface Props {
  markets: MarketRow[];
  selected: string;
  onSelect: (symbol: string) => void;
  loading: boolean;
}

export function MarketList({ markets, selected, onSelect, loading }: Props) {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  // The list is long; deferring keeps typing responsive while it re-filters.
  const deferredQuery = useDeferredValue(query);

  const visible = useMemo(() => {
    const needle = deferredQuery.trim().toUpperCase();
    if (!needle) return markets;
    return markets.filter(
      (row) => row.base.includes(needle) || row.name.toUpperCase().includes(needle),
    );
  }, [markets, deferredQuery]);

  return (
    <section className="markets panel" aria-label="Markets">
      <div className="panel__title">
        <span>{t("markets.title")}</span>
        <span className="markets__count">{visible.length}</span>
      </div>

      <div className="markets__search">
        <span className="markets__prompt" aria-hidden="true">
          &gt;
        </span>
        <input
          type="search"
          className="markets__input"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t("markets.filter")}
          aria-label={t("markets.filterLabel")}
          autoComplete="off"
          spellCheck={false}
        />
      </div>

      <ol className="markets__list">
        {loading && markets.length === 0 && (
          <li className="markets__placeholder">{t("markets.loading")}</li>
        )}
        {!loading && visible.length === 0 && (
          <li className="markets__placeholder">{t("markets.empty")}</li>
        )}

        {visible.map((row) => (
          <li key={row.symbol}>
            <button
              type="button"
              className={`markets__row${row.symbol === selected ? " markets__row--active" : ""}`}
              onClick={() => onSelect(row.symbol)}
              aria-current={row.symbol === selected}
            >
              <span className="markets__rank">
                {row.market_cap_rank ? String(row.market_cap_rank).padStart(3, "0") : "---"}
              </span>
              <span className="markets__symbol">
                <span className="markets__base">{row.base}</span>
                <span className="markets__name">{row.name}</span>
              </span>
              <span className="markets__numbers">
                <span className="markets__price">{price(row.price)}</span>
                <span className={`markets__change ${signClass(row.change_24h)}`}>
                  {percent(row.change_24h)}
                </span>
              </span>
              <span className="markets__volume" title={t("markets.volumeHint")}>
                {compact(row.volume_24h)}
              </span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}
