import type { MarketRow, Stats } from "../api/types";
import { compact, percent, price, shortDate, signClass } from "../lib/format";
import "./CoinHeader.css";

interface Props {
  symbol: string;
  market: MarketRow | undefined;
  stats: Stats | null;
}

export function CoinHeader({ symbol, market, stats }: Props) {
  const last = stats?.price.last ?? market?.price ?? null;
  const change = stats?.price.change_1d ?? market?.change_24h ?? null;

  const deltas = [
    { key: "24H", value: stats?.price.change_1d ?? market?.change_24h ?? null },
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
            {market?.name ?? "—"}
            {market?.market_cap_rank != null && (
              <span className="coin__rank">RANK #{market.market_cap_rank}</span>
            )}
          </p>
        </div>

        <div className="coin__quote">
          <span className={`coin__price ${signClass(change)}`}>{price(last)}</span>
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

      <dl className="coin__facts">
        <Fact label="MKT CAP" value={market?.market_cap != null ? `$${compact(market.market_cap)}` : "——"} />
        <Fact label="VOL 24H" value={market?.volume_24h != null ? `$${compact(market.volume_24h)}` : "——"} />
        <Fact label="ATH" value={market?.ath != null ? `$${price(market.ath)}` : "——"} />
        <Fact
          label="FROM ATH"
          value={percent(market?.ath_change)}
          tone={signClass(market?.ath_change)}
        />
        <Fact label="BARS" value={stats ? String(stats.bars) : "——"} />
        <Fact label="SINCE" value={shortDate(stats?.period_start)} />
        <Fact label="FEED" value={(stats?.source ?? market?.source ?? "—").toUpperCase()} />
      </dl>
    </section>
  );
}

function Fact({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="coin__fact">
      <dt className="coin__fact-label">{label}</dt>
      <dd className={`coin__fact-value ${tone ?? ""}`}>{value}</dd>
    </div>
  );
}
