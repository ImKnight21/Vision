import type { MarketRow, Stats } from "../api/types";
import { useI18n } from "../i18n/useI18n";
import { percent, price, signClass } from "../lib/format";
import "./CoinHeader.css";

interface Props {
  symbol: string;
  market: MarketRow | undefined;
  stats: Stats | null;
  /** Close of the forming bar, when the live poll is delivering one. */
  livePrice?: number | null;
}

export function CoinHeader({ symbol, market, stats, livePrice }: Props) {
  const { t } = useI18n();
  // The live close is the most current figure available; the loaded history
  // and the market ticker are both minutes old by comparison.
  const last = livePrice ?? stats?.price.last ?? market?.price ?? null;

  const deltas = [
    { key: "24H", value: market?.change_24h ?? stats?.price.change_1d ?? null },
    { key: "7D", value: stats?.price.change_7d ?? market?.change_7d ?? null },
    { key: "30D", value: stats?.price.change_30d ?? market?.change_30d ?? null },
    { key: "90D", value: stats?.price.change_90d ?? null },
  ];

  return (
    <section className="coin panel panel--bracketed">
      <div className="coin__identity">
        <div className="coin__names">
          <h2 className="coin__symbol">{symbol}</h2>
          <p className="coin__name">
            {market?.name ?? "--"}
            {market?.market_cap_rank != null && (
              <span className="coin__rank">{t("coin.rank")} #{market.market_cap_rank}</span>
            )}
          </p>
        </div>

        <div className="coin__quote">
          <span className="coin__price">{price(last)}</span>
          <span className="coin__quote-unit">USDT</span>
        </div>
      </div>

      <ul className="coin__deltas">
        {deltas.map((delta) => (
          <li key={delta.key} className="coin__delta">
            <span className="coin__delta-key">{delta.key}</span>
            <span className={`coin__delta-value ${signClass(delta.value)}`}>
              {percent(delta.value)}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
