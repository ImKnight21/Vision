import type { MarketRow, Stats } from "../api/types";
import { Stable } from "../i18n/Stable";
import type { StringKey } from "../i18n/dictionary";
import { compact, percent, price, shortDate, signClass } from "../lib/format";
import "./CoinFacts.css";

interface Props {
  market: MarketRow | undefined;
  stats: Stats | null;
}

/**
 * Reference data about the coin: what it is worth in total, how far it is off
 * its high, and where the numbers came from.
 *
 * A separate section from `CoinHeader` so that the two can be reordered
 * independently. On a phone the chart is what the page is for, and it used to
 * sit roughly 900px below the fold behind this block; here it is a sibling of
 * the chart and CSS `order` puts it underneath.
 */
export function CoinFacts({ market, stats }: Props) {
  return (
    <section className="facts panel panel--bracketed">
      <dl className="facts__grid">
        <Fact
          label="coin.marketCap"
          value={market?.market_cap != null ? `$${compact(market.market_cap)}` : "--"}
        />
        <Fact
          label="coin.volume24h"
          value={market?.volume_24h != null ? `$${compact(market.volume_24h)}` : "--"}
        />
        <Fact
          label="coin.ath"
          value={market?.ath != null ? `$${price(market.ath)}` : "--"}
        />
        <Fact
          label="coin.fromAth"
          value={percent(market?.ath_change)}
          tone={signClass(market?.ath_change)}
        />
        <Fact label="coin.bars" value={stats ? String(stats.bars) : "--"} />
        <Fact label="coin.since" value={shortDate(stats?.period_start)} />
        <Fact
          label="coin.feed"
          value={(stats?.source ?? market?.source ?? "--").toUpperCase()}
        />
      </dl>
    </section>
  );
}

function Fact({
  label,
  value,
  tone,
}: {
  label: StringKey;
  value: string;
  tone?: string;
}) {
  return (
    <div className="facts__item">
      <dt className="facts__label">
        <Stable show={label} />
      </dt>
      <dd className={`facts__value ${tone ?? ""}`}>{value}</dd>
    </div>
  );
}
