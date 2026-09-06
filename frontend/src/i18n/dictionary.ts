/**
 * UI strings, English and Russian.
 *
 * English is the source of truth: `Russian` is typed as a record over its keys,
 * so a missing or stray translation is a compile error rather than a stray
 * English label discovered in a screenshot.
 *
 * Numbers are deliberately *not* localised. Prices, ratios and percentages stay
 * in the international format (comma thousands, dot decimal) in both languages,
 * because that is what every exchange and terminal shows and a Russian-style
 * decimal comma next to a thousands space reads as two different numbers.
 */

export const en = {
  // --- chrome ---
  "brand.subtitle": "MARKET TERMINAL",
  "header.markets": "[ MARKETS ]",
  "header.tube": "TUBE",
  "header.fx": "FX",
  "header.fxHint":
    "Scanlines, vignette and glow. Turn them off for a flat, maximally legible screen.",
  "header.lang": "LANG",
  "header.langHint": "Switch the interface language.",
  "status.live": "ONLINE",
  "status.loading": "SYNC",
  "status.error": "NO LINK",
  "status.waking": "WAKING THE BACKEND",
  "status.wakingHint":
    "The API runs on a free instance that sleeps after 15 minutes of quiet. The first request after that wakes it, which takes up to a minute. Later loads are instant.",

  // --- market list ---
  "markets.title": "MARKETS",
  "markets.filter": "FILTER SYMBOL",
  "markets.filterLabel": "Filter markets",
  "markets.loading": "LOADING FEED...",
  "markets.empty": "NO MATCH",
  "markets.volumeHint": "24h quote volume",

  // --- coin header ---
  "coin.rank": "RANK",
  "coin.marketCap": "MKT CAP",
  "coin.volume24h": "VOL 24H",
  "coin.ath": "ATH",
  "coin.fromAth": "FROM ATH",
  "coin.bars": "BARS",
  "coin.since": "SINCE",
  "coin.feed": "FEED",

  // --- controls ---
  "controls.interval": "INTERVAL",
  "controls.bars": "BARS",
  "controls.overlay": "OVERLAY",
  "controls.volume": "VOL",
  "controls.movingAverages": "MA 50/200",

  // --- chart ---
  "chart.empty": "NO SIGNAL",
  "chart.label": "Price chart",
  "chart.open": "O",
  "chart.high": "H",
  "chart.low": "L",
  "chart.close": "C",
  "chart.volume": "VOL",
  "chart.change": "CHG",
  "chart.live": "LIVE",
  "chart.liveHint": "The candle currently forming. It is not closed yet.",

  // --- panels ---
  "panel.volatility": "VOLATILITY",
  "panel.volatilityNote": "annualised",
  "panel.risk": "RISK & DRAWDOWN",
  "panel.tail": "TAIL RISK",
  "panel.tailNote": "per bar",
  "panel.distribution": "DISTRIBUTION",
  "panel.indicators": "INDICATORS",
  "panel.regime": "REGIME",
  "panel.liquidity": "LIQUIDITY",
  "panel.relative": "VS BITCOIN",
  "panel.compare": "COMPARE",

  // --- volatility ---
  "vol.realized7d": "Realized 7d",
  "vol.realized30d": "Realized 30d",
  "vol.realized90d": "Realized 90d",
  "vol.realizedAll": "Realized all",
  "vol.ewma": "EWMA",
  "vol.parkinson": "Parkinson 30d",
  "vol.garmanKlass": "Garman-Klass 30d",
  "vol.rogersSatchell": "Rogers-Satchell 30d",
  "vol.realized7dHint":
    "Annualised standard deviation of log returns over the last 7 days.",
  "vol.realized30dHint": "The same measure over 30 days, the usual reference window.",
  "vol.realized90dHint": "Over 90 days: slower to react, but far less noisy.",
  "vol.realizedAllHint": "Over the whole loaded history.",
  "vol.ewmaHint":
    "Exponentially weighted, lambda 0.94. Reacts to a regime change faster than a fixed window. Far above the 30d figure means volatility is rising right now.",
  "vol.parkinsonHint":
    "Uses the high-low range instead of closes: more precise, but blind to gaps between bars.",
  "vol.garmanKlassHint":
    "Uses the full OHLC bar. The most efficient estimator when price is not trending.",
  "vol.rogersSatchellHint":
    "The range estimator that stays unbiased while price trends. Trust this one during a strong run.",

  // --- risk ---
  "risk.sharpe": "Sharpe",
  "risk.sortino": "Sortino",
  "risk.calmar": "Calmar",
  "risk.maxDrawdown": "Max drawdown",
  "risk.currentDrawdown": "Current drawdown",
  "risk.trough": "Trough",
  "risk.recovered": "Recovered",
  "risk.notYet": "NOT YET",
  "risk.ulcer": "Ulcer index",
  "risk.underwaterShare": "Time under water",
  "risk.underwaterLongest": "Longest slump",
  "risk.recoveryFactor": "Recovery factor",
  "risk.sharpeHint":
    "Annualised return per unit of total volatility. Above 1 is strong; below 0 means the asset lost money.",
  "risk.sortinoHint":
    "Like Sharpe, but only downside moves count as risk. Higher than Sharpe means the swings were mostly upward.",
  "risk.calmarHint":
    "Annualised return divided by the worst drawdown: how much you earned per unit of pain.",
  "risk.maxDrawdownHint": "The deepest peak-to-trough fall inside this window.",
  "risk.currentDrawdownHint": "How far below the window's high the price sits right now.",
  "risk.troughHint": "When the deepest point was reached.",
  "risk.recoveredHint": "When price first closed back at the pre-drawdown peak.",
  "risk.ulcerHint":
    "Root-mean-square drawdown: depth and duration in one number. Max drawdown reports the worst moment; this reports how deep the water was on average.",
  "risk.underwaterShareHint":
    "Share of bars spent below a previous high. An asset can post a fine return and still have been underwater almost the whole time.",
  "risk.underwaterLongestHint":
    "The longest unbroken stretch below a previous high, in days.",
  "risk.recoveryFactorHint":
    "Window return divided by the depth of the worst drawdown.",
  "risk.drawdownMeter": "Depth of current drawdown",
  "risk.atHigh": "AT HIGH",
  "risk.atWorst": "AT WORST",
  "risk.drawdownMeterHint":
    "Where the present drawdown sits between the window's high and its deepest point.",

  // --- tail risk ---
  "tail.var95": "VaR 95%",
  "tail.cvar95": "CVaR 95%",
  "tail.var99": "VaR 99%",
  "tail.cvar99": "CVaR 99%",
  "tail.worst": "Worst bar",
  "tail.best": "Best bar",
  "tail.ratio": "Tail ratio",
  "tail.omega": "Omega",
  "tail.var95Hint": "On the worst 1 bar in 20, the loss was at least this large.",
  "tail.cvar95Hint":
    "Average loss across those worst 5% of bars: how bad the bad days actually get.",
  "tail.var99Hint": "The same idea for the worst 1 bar in 100.",
  "tail.cvar99Hint": "Average loss inside that extreme 1% tail.",
  "tail.worstHint": "Largest single-bar loss in the window.",
  "tail.bestHint": "Largest single-bar gain in the window.",
  "tail.ratioHint":
    "Size of the best tail against the worst. Above 1 means the good outliers were bigger than the bad ones.",
  "tail.omegaHint":
    "Total gains divided by total losses. Uses the whole distribution, so unlike Sharpe it does not assume returns are normal.",

  // --- distribution ---
  "dist.skew": "Skew",
  "dist.kurtosis": "Excess kurtosis",
  "dist.upBars": "Up bars",
  "dist.totalReturn": "Total return",
  "dist.cagr": "CAGR",
  "dist.gainToPain": "Gain to pain",
  "dist.skewHint":
    "Asymmetry of returns. Negative means the outsized moves tend to be crashes.",
  "dist.kurtosisHint":
    "Tail weight versus a normal distribution. Above 0 means outliers are more common than a bell curve predicts.",
  "dist.upBarsHint": "Share of bars that closed higher than the one before.",
  "dist.totalReturnHint": "Change over the entire loaded window.",
  "dist.cagrHint": "That same return expressed as an annual compounding rate.",
  "dist.gainToPainHint":
    "Sum of all returns divided by the sum of the losing ones: did the winners pay for the losers?",

  // --- regime ---
  "regime.hurst": "Hurst",
  "regime.autocorrelation": "Autocorrelation",
  "regime.volPercentile": "Vol percentile",
  "regime.volOfVol": "Vol of vol",
  "regime.trendStrength": "Trend strength",
  "regime.trendChange": "Trend change 50",
  "regime.hurstHint":
    "0.5 is a random walk. Above 0.5 moves persist, so breakouts tend to follow through; below 0.5 they get given back, so fades work better.",
  "regime.autocorrelationHint":
    "Correlation of each bar with the one before. Positive means momentum, negative means reversal. The sign matters more than the size.",
  "regime.volPercentileHint":
    "Where current volatility sits in this coin's own history. 60% annualised means nothing alone; 60% at the 95th percentile means it is as agitated as it ever gets.",
  "regime.volOfVolHint":
    "How unstable the volatility itself is. High means the coin switches between calm and violent regimes, so any single volatility figure has a short shelf life.",
  "regime.trendStrengthHint":
    "R-squared of a straight line through log price: how orderly the move is, not which way. High means a clean run, low means chop that drifted.",
  "regime.trendChangeHint":
    "How far the fitted trend line travelled over the last 50 bars. Deliberately not annualised. Read it beside trend strength.",
  "regime.meter": "Trend vs mean-reversion",
  "regime.reverting": "REVERTS 0.3",
  "regime.trending": "0.7 TRENDS",

  // --- liquidity ---
  "liq.impact": "Impact per $1M",
  "liq.volumeZ": "Volume z-score",
  "liq.volumeTrend": "Volume trend",
  "liq.medianVolume": "Median volume",
  "liq.minVolume": "Thinnest day",
  "liq.impactHint":
    "How far the price moves per $1M traded. Higher means thinner: the same order pushes price further. Compare across coins, not against a threshold.",
  "liq.volumeZHint":
    "How unusual the latest bar's turnover is, in standard deviations. Above 2 is a spike; a breakout on below-average volume is the one to distrust.",
  "liq.volumeTrendHint":
    "Recent turnover over its longer-run average. Below 1 during a price rise means the move is running on fewer participants.",
  "liq.medianVolumeHint":
    "Typical daily turnover over 30 bars. The median, so one listing-day spike does not describe an ordinary day.",
  "liq.minVolumeHint": "The quietest day in the window: the liquidity you can rely on.",

  // --- relative ---
  "rel.correlation": "Correlation",
  "rel.beta": "Beta",
  "rel.alpha": "Alpha",
  "rel.rSquared": "R-squared",
  "rel.trackingError": "Tracking error",
  "rel.upCapture": "Up capture",
  "rel.downCapture": "Down capture",
  "rel.relativeReturn": "Relative return",
  "rel.correlationHint":
    "How closely this coin moves with Bitcoin. Near 1 means it offers almost no diversification.",
  "rel.betaHint":
    "Move per 1% move in Bitcoin. Above 1 amplifies the market in both directions.",
  "rel.alphaHint":
    "Annualised return left over once the Bitcoin exposure that beta describes has been paid for. Negative means the coin underperformed the risk it carried.",
  "rel.rSquaredHint":
    "Share of this coin's movement explained by Bitcoin. High means it is essentially a leveraged BTC position.",
  "rel.trackingErrorHint": "How far this coin's path strays from Bitcoin's, annualised.",
  "rel.upCaptureHint":
    "Share of Bitcoin's gain captured on its up bars. Above 1 means it rallies harder.",
  "rel.downCaptureHint":
    "Share of Bitcoin's fall taken on its down bars. Below 1 is the good case; above 1 with a similar up capture is just leverage.",
  "rel.relativeReturnHint": "Total return minus Bitcoin's over the same window.",
  "rel.isBenchmark": "This is the benchmark.",

  // --- indicators ---
  "ind.rsi": "RSI 14",
  "ind.atr": "ATR 14",
  "ind.atrPercent": "ATR %",
  "ind.sma20": "SMA 20",
  "ind.sma50": "SMA 50",
  "ind.sma200": "SMA 200",
  "ind.bbWidth": "BB width",
  "ind.rsiHint":
    "Momentum on a 0-100 scale. Above 70 is conventionally overbought, below 30 oversold.",
  "ind.atrHint": "Average true range in price units: how far a typical bar travels.",
  "ind.atrPercentHint":
    "The same range as a share of price, so it can be compared across coins.",
  "ind.sma200Hint": "The long-term trend line most desks watch.",
  "ind.bbWidthHint":
    "Bollinger band width relative to price. Narrow bands often precede a large move.",
  "ind.oversold": "30 OVERSOLD",
  "ind.overbought": "OVERBOUGHT 70",
  "ind.range30d": "Position in 30d range",
  "ind.range365d": "Position in 1y range",
  "ind.range30dHint": "Where the last price sits between the 30-day low and high.",
  "ind.range365dHint": "The same, measured over a year of bars.",

  // --- comparison ---
  "compare.title": "CORRELATION",
  "compare.subtitle": "shared bars",
  "compare.add": "ADD COIN",
  "compare.remove": "Remove",
  "compare.empty": "Pick at least two coins to compare.",
  "compare.matrixHint":
    "Pairwise correlation of daily returns. Near 1 means the pair moves as one, so holding both diversifies little.",
  "compare.symbol": "SYMBOL",
  "compare.volatility": "VOL 30D",
  "compare.sharpe": "SHARPE",
  "compare.maxDrawdown": "MAX DD",
  "compare.beta": "BETA",
  "compare.correlation": "CORR",
  "compare.hurst": "HURST",
  "compare.totalReturn": "RETURN",
  "compare.failed": "Could not load",
  "compare.open": "COMPARE",
  "compare.close": "CLOSE",

  // --- misc ---
  "common.retry": "[ RETRY ]",
  "common.error": "ERR",
  "common.noData": "--",
  "common.days": "d",
  "disclaimer":
    "Informational only. Every figure is derived from historical candles and says nothing about what happens next.",
} as const;

export type StringKey = keyof typeof en;

export const ru: Record<StringKey, string> = {
  "brand.subtitle": "РЫНОЧНЫЙ ТЕРМИНАЛ",
  "header.markets": "[ РЫНКИ ]",
  "header.tube": "ТРУБКА",
  "header.fx": "ЭФФЕКТЫ",
  "header.fxHint":
    "Строки развёртки, виньетка и свечение. Выключите для плоского, максимально читаемого экрана.",
  "header.lang": "ЯЗЫК",
  "header.langHint": "Переключить язык интерфейса.",
  "status.live": "НА СВЯЗИ",
  "status.loading": "ОБМЕН",
  "status.error": "НЕТ СВЯЗИ",
  "status.waking": "БУДИМ СЕРВЕР",
  "status.wakingHint":
    "API работает на бесплатном сервере, который засыпает после 15 минут тишины. Первый запрос его будит, это занимает до минуты. Дальше загрузка мгновенная.",

  "markets.title": "РЫНКИ",
  "markets.filter": "ПОИСК ТИКЕРА",
  "markets.filterLabel": "Фильтр рынков",
  "markets.loading": "ЗАГРУЗКА...",
  "markets.empty": "НЕ НАЙДЕНО",
  "markets.volumeHint": "Оборот за 24 часа в котируемой валюте",

  "coin.rank": "МЕСТО",
  "coin.marketCap": "КАПИТАЛИЗАЦИЯ",
  "coin.volume24h": "ОБЪЁМ 24Ч",
  "coin.ath": "МАКСИМУМ",
  "coin.fromAth": "ОТ МАКСИМУМА",
  "coin.bars": "СВЕЧЕЙ",
  "coin.since": "С ДАТЫ",
  "coin.feed": "ИСТОЧНИК",

  "controls.interval": "ИНТЕРВАЛ",
  "controls.bars": "СВЕЧЕЙ",
  "controls.overlay": "СЛОИ",
  "controls.volume": "ОБЪЁМ",
  "controls.movingAverages": "СС 50/200",

  "chart.empty": "НЕТ СИГНАЛА",
  "chart.label": "График цены",
  "chart.open": "О",
  "chart.high": "В",
  "chart.low": "Н",
  "chart.close": "З",
  "chart.volume": "ОБЪЁМ",
  "chart.change": "ИЗМ",
  "chart.live": "СЕЙЧАС",
  "chart.liveHint": "Текущая формирующаяся свеча. Она ещё не закрыта.",

  "panel.volatility": "ВОЛАТИЛЬНОСТЬ",
  "panel.volatilityNote": "годовая",
  "panel.risk": "РИСК И ПРОСАДКИ",
  "panel.tail": "ХВОСТОВОЙ РИСК",
  "panel.tailNote": "на свечу",
  "panel.distribution": "РАСПРЕДЕЛЕНИЕ",
  "panel.indicators": "ИНДИКАТОРЫ",
  "panel.regime": "РЕЖИМ РЫНКА",
  "panel.liquidity": "ЛИКВИДНОСТЬ",
  "panel.relative": "ОТНОСИТЕЛЬНО BTC",
  "panel.compare": "СРАВНЕНИЕ",

  "vol.realized7d": "Реализованная 7д",
  "vol.realized30d": "Реализованная 30д",
  "vol.realized90d": "Реализованная 90д",
  "vol.realizedAll": "За всю историю",
  "vol.ewma": "EWMA",
  "vol.parkinson": "Паркинсон 30д",
  "vol.garmanKlass": "Гарман-Класс 30д",
  "vol.rogersSatchell": "Роджерс-Сатчелл 30д",
  "vol.realized7dHint":
    "Годовое стандартное отклонение логарифмических доходностей за последние 7 дней.",
  "vol.realized30dHint": "То же за 30 дней. Основное окно для сравнения.",
  "vol.realized90dHint": "За 90 дней: реагирует медленнее, но заметно меньше шума.",
  "vol.realizedAllHint": "За всю загруженную историю.",
  "vol.ewmaHint":
    "Экспоненциально взвешенная, лямбда 0.94. Реагирует на смену режима быстрее фиксированного окна. Заметно выше 30-дневной означает, что волатильность растёт прямо сейчас.",
  "vol.parkinsonHint":
    "Использует диапазон максимум-минимум вместо закрытий: точнее, но не видит разрывов между свечами.",
  "vol.garmanKlassHint":
    "Использует всю свечу. Самая эффективная оценка, когда цена не в тренде.",
  "vol.rogersSatchellHint":
    "Единственная диапазонная оценка, не смещающаяся при тренде. На сильном движении доверять стоит именно ей.",

  "risk.sharpe": "Шарп",
  "risk.sortino": "Сортино",
  "risk.calmar": "Калмар",
  "risk.maxDrawdown": "Макс. просадка",
  "risk.currentDrawdown": "Текущая просадка",
  "risk.trough": "Дно",
  "risk.recovered": "Восстановление",
  "risk.notYet": "НЕ БЫЛО",
  "risk.ulcer": "Индекс язвы",
  "risk.underwaterShare": "Время под водой",
  "risk.underwaterLongest": "Самый долгий спад",
  "risk.recoveryFactor": "Фактор восстановления",
  "risk.sharpeHint":
    "Годовая доходность на единицу общей волатильности. Выше 1 хорошо; ниже 0 означает, что актив принёс убыток.",
  "risk.sortinoHint":
    "Как Шарп, но риском считаются только движения вниз. Выше Шарпа означает, что колебания были в основном вверх.",
  "risk.calmarHint":
    "Годовая доходность, делённая на худшую просадку: сколько заработано на единицу боли.",
  "risk.maxDrawdownHint": "Самое глубокое падение от пика до дна в этом окне.",
  "risk.currentDrawdownHint": "Насколько ниже максимума окна цена находится сейчас.",
  "risk.troughHint": "Когда была достигнута нижняя точка.",
  "risk.recoveredHint": "Когда цена впервые закрылась обратно на уровне пика до просадки.",
  "risk.ulcerHint":
    "Среднеквадратичная просадка: глубина и длительность в одном числе. Максимальная просадка описывает худший момент, а этот индекс, насколько глубока была вода в среднем.",
  "risk.underwaterShareHint":
    "Доля свечей ниже предыдущего максимума. Актив может показать неплохую доходность и при этом почти всё время быть под водой.",
  "risk.underwaterLongestHint":
    "Самый длинный непрерывный период ниже предыдущего максимума, в днях.",
  "risk.recoveryFactorHint":
    "Доходность за окно, делённая на глубину худшей просадки.",
  "risk.drawdownMeter": "Глубина текущей просадки",
  "risk.atHigh": "НА ПИКЕ",
  "risk.atWorst": "НА ДНЕ",
  "risk.drawdownMeterHint":
    "Где текущая просадка находится между максимумом окна и самой глубокой его точкой.",

  "tail.var95": "VaR 95%",
  "tail.cvar95": "CVaR 95%",
  "tail.var99": "VaR 99%",
  "tail.cvar99": "CVaR 99%",
  "tail.worst": "Худшая свеча",
  "tail.best": "Лучшая свеча",
  "tail.ratio": "Отношение хвостов",
  "tail.omega": "Омега",
  "tail.var95Hint": "В худшей свече из двадцати убыток был не меньше этого.",
  "tail.cvar95Hint":
    "Средний убыток в этих худших 5% свечей: насколько плохи плохие дни на самом деле.",
  "tail.var99Hint": "То же для худшей свечи из ста.",
  "tail.cvar99Hint": "Средний убыток внутри этого крайнего 1% хвоста.",
  "tail.worstHint": "Наибольший убыток за одну свечу в окне.",
  "tail.bestHint": "Наибольшая прибыль за одну свечу в окне.",
  "tail.ratioHint":
    "Размер лучшего хвоста против худшего. Выше 1 означает, что хорошие выбросы были крупнее плохих.",
  "tail.omegaHint":
    "Сумма прибылей, делённая на сумму убытков. Использует всё распределение, поэтому в отличие от Шарпа не предполагает нормальность.",

  "dist.skew": "Асимметрия",
  "dist.kurtosis": "Избыточный эксцесс",
  "dist.upBars": "Растущих свечей",
  "dist.totalReturn": "Общая доходность",
  "dist.cagr": "Годовая доходность",
  "dist.gainToPain": "Прибыль к боли",
  "dist.skewHint":
    "Асимметрия доходностей. Отрицательная означает, что крупные движения чаще обвалы.",
  "dist.kurtosisHint":
    "Вес хвостов относительно нормального распределения. Выше 0 означает, что выбросы случаются чаще, чем предсказывает колокол.",
  "dist.upBarsHint": "Доля свечей, закрывшихся выше предыдущей.",
  "dist.totalReturnHint": "Изменение за всё загруженное окно.",
  "dist.cagrHint": "Та же доходность, выраженная как годовая ставка сложного процента.",
  "dist.gainToPainHint":
    "Сумма всех доходностей, делённая на сумму убыточных: окупили ли выигрыши проигрыши?",

  "regime.hurst": "Хёрст",
  "regime.autocorrelation": "Автокорреляция",
  "regime.volPercentile": "Перцентиль вол-ти",
  "regime.volOfVol": "Вол-ть волатильности",
  "regime.trendStrength": "Сила тренда",
  "regime.trendChange": "Движение тренда 50",
  "regime.hurstHint":
    "0.5 означает случайное блуждание. Выше 0.5 движения продолжаются, поэтому пробои чаще отрабатывают; ниже 0.5 движения откатываются, и лучше работает торговля против них.",
  "regime.autocorrelationHint":
    "Корреляция каждой свечи с предыдущей. Положительная означает инерцию, отрицательная разворот. Знак важнее величины.",
  "regime.volPercentileHint":
    "Где текущая волатильность находится в собственной истории монеты. 60% годовых сами по себе ничего не значат; 60% на 95-м перцентиле означают, что монета возбуждена почти как никогда.",
  "regime.volOfVolHint":
    "Насколько нестабильна сама волатильность. Высокое значение означает, что монета переключается между спокойными и бурными режимами, поэтому у любой одной оценки короткий срок годности.",
  "regime.trendStrengthHint":
    "R-квадрат прямой, проведённой через логарифм цены: насколько движение упорядочено, а не куда направлено. Высокое значение означает чистый ход, низкое пилу, которую снесло в сторону.",
  "regime.trendChangeHint":
    "Насколько сместилась подогнанная линия тренда за последние 50 свечей. Намеренно не приведено к году. Читать вместе с силой тренда.",
  "regime.meter": "Тренд против возврата к среднему",
  "regime.reverting": "ВОЗВРАТ 0.3",
  "regime.trending": "0.7 ТРЕНД",

  "liq.impact": "Влияние на $1 млн",
  "liq.volumeZ": "Z-оценка объёма",
  "liq.volumeTrend": "Тренд объёма",
  "liq.medianVolume": "Медианный объём",
  "liq.minVolume": "Самый тонкий день",
  "liq.impactHint":
    "Насколько сдвигается цена на каждый $1 млн оборота. Чем выше, тем тоньше рынок: та же заявка двигает цену дальше. Сравнивать между монетами, а не с абсолютным порогом.",
  "liq.volumeZHint":
    "Насколько необычен оборот последней свечи, в стандартных отклонениях. Выше 2 это всплеск. Пробой на объёме ниже среднего доверия не заслуживает.",
  "liq.volumeTrendHint":
    "Недавний оборот относительно среднего за более длинный период. Ниже 1 при росте цены означает, что движение держится на всё меньшем числе участников.",
  "liq.medianVolumeHint":
    "Типичный дневной оборот за 30 свечей. Именно медиана, чтобы один всплеск не выдавал себя за обычный день.",
  "liq.minVolumeHint":
    "Самый тихий день в окне: ликвидность, на которую можно рассчитывать.",

  "rel.correlation": "Корреляция",
  "rel.beta": "Бета",
  "rel.alpha": "Альфа",
  "rel.rSquared": "R-квадрат",
  "rel.trackingError": "Ошибка слежения",
  "rel.upCapture": "Захват роста",
  "rel.downCapture": "Захват падения",
  "rel.relativeReturn": "Относительная доходность",
  "rel.correlationHint":
    "Насколько тесно монета движется вместе с биткоином. Близко к 1 означает, что диверсификации она почти не даёт.",
  "rel.betaHint":
    "Движение на каждый 1% движения биткоина. Выше 1 усиливает рынок в обе стороны.",
  "rel.alphaHint":
    "Годовая доходность, оставшаяся после оплаты той зависимости от биткоина, которую описывает бета. Отрицательная означает, что монета не отработала принятый риск.",
  "rel.rSquaredHint":
    "Доля движения монеты, объяснённая биткоином. Высокая означает, что это по сути позиция в BTC с плечом.",
  "rel.trackingErrorHint":
    "Насколько путь монеты отклоняется от пути биткоина, в годовом выражении.",
  "rel.upCaptureHint":
    "Какую долю роста биткоина монета забирает на его растущих свечах. Выше 1 означает, что растёт сильнее.",
  "rel.downCaptureHint":
    "Какую долю падения биткоина монета принимает на его падающих свечах. Ниже 1 это хороший случай. Выше 1 при похожем захвате роста означает просто плечо.",
  "rel.relativeReturnHint": "Общая доходность минус доходность биткоина за то же окно.",
  "rel.isBenchmark": "Это и есть эталон.",

  "ind.rsi": "RSI 14",
  "ind.atr": "ATR 14",
  "ind.atrPercent": "ATR %",
  "ind.sma20": "СС 20",
  "ind.sma50": "СС 50",
  "ind.sma200": "СС 200",
  "ind.bbWidth": "Ширина Боллинджера",
  "ind.rsiHint":
    "Импульс по шкале 0-100. Выше 70 принято считать перекупленностью, ниже 30, перепроданностью.",
  "ind.atrHint":
    "Средний истинный диапазон в единицах цены: насколько далеко проходит обычная свеча.",
  "ind.atrPercentHint":
    "Тот же диапазон как доля цены, чтобы можно было сравнивать разные монеты.",
  "ind.sma200Hint": "Долгосрочная линия тренда, за которой следит большинство.",
  "ind.bbWidthHint":
    "Ширина полос Боллинджера относительно цены. Узкие полосы часто предшествуют крупному движению.",
  "ind.oversold": "30 ПЕРЕПРОДАН",
  "ind.overbought": "ПЕРЕКУПЛЕН 70",
  "ind.range30d": "Позиция в диапазоне 30д",
  "ind.range365d": "Позиция в диапазоне 1г",
  "ind.range30dHint":
    "Где находится последняя цена между минимумом и максимумом за 30 дней.",
  "ind.range365dHint": "То же самое, измеренное за год свечей.",

  "compare.title": "КОРРЕЛЯЦИЯ",
  "compare.subtitle": "общих свечей",
  "compare.add": "ДОБАВИТЬ",
  "compare.remove": "Убрать",
  "compare.empty": "Выберите хотя бы две монеты для сравнения.",
  "compare.matrixHint":
    "Попарная корреляция дневных доходностей. Близко к 1 означает, что пара движется как одно целое, и держать обе почти не даёт диверсификации.",
  "compare.symbol": "ТИКЕР",
  "compare.volatility": "ВОЛ 30Д",
  "compare.sharpe": "ШАРП",
  "compare.maxDrawdown": "МАКС ПРОС",
  "compare.beta": "БЕТА",
  "compare.correlation": "КОРР",
  "compare.hurst": "ХЁРСТ",
  "compare.totalReturn": "ДОХОД",
  "compare.failed": "Не загрузилось",
  "compare.open": "СРАВНИТЬ",
  "compare.close": "ЗАКРЫТЬ",

  "common.retry": "[ ПОВТОР ]",
  "common.error": "ОШБ",
  "common.noData": "--",
  "common.days": "д",
  "disclaimer":
    "Только для ознакомления. Каждая цифра рассчитана по историческим свечам и ничего не говорит о том, что будет дальше.",
};

export const dictionaries = { en, ru } as const;
export type Locale = keyof typeof dictionaries;
