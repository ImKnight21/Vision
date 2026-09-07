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
  /** Bybit publishes no spot trade count, so this is absent on its rows. */
  trades_24h: number | null;
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

/** The tail of the series, polled on a timer to keep the chart current. */
export interface Latest {
  symbol: string;
  interval: string;
  source: string;
  /** The forming bar, preceded by the one before it. */
  candles: Candle[];
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
    ulcer_index: number | null;
    underwater_share: number | null;
    underwater_longest_days: number | null;
    underwater_current_days: number | null;
    recovery_factor: number | null;
    tail_ratio: number | null;
    omega: number | null;
    gain_to_pain: number | null;
  };
  regime: {
    /** 0.5 is a random walk; above trends, below mean-reverts. */
    hurst: number | null;
    autocorrelation: number | null;
    vol_of_vol: number | null;
    /** Where current volatility sits in this coin's own history, 0..1. */
    vol_percentile: number | null;
    trend_strength: number | null;
    trend_change: number | null;
  };
  liquidity: {
    /** Fractional price move per $1M of volume. */
    amihud: number | null;
    volume_zscore: number | null;
    volume_trend: number | null;
    dollar_volume_median: number | null;
    dollar_volume_min: number | null;
  };
  /** Null when the coin is itself the benchmark, or the benchmark failed. */
  relative: RelativeStats | null;
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

export interface RelativeStats {
  benchmark: string;
  bars: number;
  correlation: number | null;
  beta: number | null;
  alpha: number | null;
  r_squared: number | null;
  tracking_error: number | null;
  up_capture: number | null;
  down_capture: number | null;
  relative_return: number | null;
}

export interface CompareRow {
  symbol: string;
  last: number | null;
  total_return: number | null;
  volatility_30d: number | null;
  sharpe: number | null;
  max_drawdown: number | null;
  hurst: number | null;
  beta: number | null;
  correlation: number | null;
  alpha: number | null;
}

export interface Comparison {
  interval: string;
  benchmark: string | null;
  failed: string[];
  rows: CompareRow[];
  symbols: string[];
  bars: number;
  /** Square matrix in `symbols` order; null when there was too little overlap. */
  matrix: (number | null)[][] | null;
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
