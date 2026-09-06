/** Shapes returned by the Vision API. Fractions, not percents: 0.0241 is +2.41%. */

export interface MarketRow {
  symbol: string;
  base: string;
  quote: string;
  name: string;
  image: string | null;
  coingecko_id: string | null;
  price: number;
  change_24h: number;
  change_7d: number | null;
  change_30d: number | null;
  high_24h: number | null;
  low_24h: number | null;
  volume_24h: number;
  trades_24h: number;
  market_cap: number | null;
  market_cap_rank: number | null;
  circulating_supply: number | null;
  max_supply: number | null;
  ath: number | null;
  ath_change: number | null;
  source: string;
}

export interface Candle {
  time: number; // UNIX seconds
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

/** A statistic measured over several lookbacks. `all` covers the whole series. */
export interface WindowedStat {
  "7d": number | null;
  "30d": number | null;
  "90d": number | null;
  all: number | null;
}

export interface RangePosition {
  high: number | null;
  low: number | null;
  /** 0 = at the window's low, 1 = at its high. */
  position: number | null;
}

export interface Stats {
  symbol: string;
  interval: string;
  bars: number;
  source: string;
  period_start: string | null;
  period_end: string | null;
  price: {
    last: number | null;
    change_1d: number | null;
    change_7d: number | null;
    change_30d: number | null;
    change_90d: number | null;
    range_30d: RangePosition;
    range_365d: RangePosition;
  };
  returns: { total: number | null; cagr: number | null };
  volatility: {
    realized: WindowedStat;
    parkinson: WindowedStat;
    garman_klass: WindowedStat;
    rogers_satchell: WindowedStat;
    ewma: number | null;
  };
  risk: {
    sharpe: number | null;
    sortino: number | null;
    calmar: number | null;
    max_drawdown: number | null;
    current_drawdown: number | null;
    drawdown_peak_at: string | null;
    drawdown_trough_at: string | null;
    drawdown_recovered_at: string | null;
    var_95: number | null;
    cvar_95: number | null;
    var_99: number | null;
    cvar_99: number | null;
  };
  distribution: {
    skew: number | null;
    kurtosis: number | null;
    best: number | null;
    worst: number | null;
    positive_share: number | null;
  };
  indicators: {
    rsi_14: number | null;
    atr_14: number | null;
    atr_percent_14: number | null;
    sma_20: number | null;
    sma_50: number | null;
    sma_200: number | null;
    ema_12: number | null;
    ema_26: number | null;
    bollinger_width: number | null;
    percent_b: number | null;
  };
}

export interface Overview {
  symbol: string;
  interval: string;
  source: string;
  candles: Candle[];
  stats: Stats;
}

export interface IntervalOption {
  value: string;
  seconds: number;
}
