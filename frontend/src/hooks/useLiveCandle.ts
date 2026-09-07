import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Candle } from "../api/types";

interface Live {
  /** The newest bars, or null until the first poll answers. */
  candles: Candle[] | null;
  /** True while polling is actually running and the last poll succeeded. */
  streaming: boolean;
}

/**
 * Polls the newest bar and keeps the chart current.
 *
 * Self-scheduling rather than `setInterval`: a slow response must not let a
 * second request start before the first one finishes, which on a sleeping free
 * instance would otherwise pile up a queue of identical calls.
 *
 * Polling stops while the tab is hidden. A backgrounded chart nobody is looking
 * at should not keep a free-tier backend awake, and browsers throttle timers
 * there anyway, so the requests that did survive would arrive at unpredictable
 * intervals.
 */
export function useLiveCandle(
  symbol: string,
  interval: string,
  { every = 5000, enabled = true }: { every?: number; enabled?: boolean } = {},
): Live {
  const [state, setState] = useState<Live>({ candles: null, streaming: false });

  // Consecutive failures, used to back off. Kept in a ref so a failure does not
  // re-render on its own.
  const failures = useRef(0);

  useEffect(() => {
    if (!enabled) {
      setState({ candles: null, streaming: false });
      return;
    }

    // A new symbol or interval invalidates whatever the previous one returned;
    // leaving it on screen would draw one coin's bar onto another's chart.
    setState({ candles: null, streaming: false });

    let stopped = false;
    let timer: number | undefined;
    let controller: AbortController | null = null;

    const tick = async () => {
      if (stopped) return;
      if (document.visibilityState !== "visible") {
        // Check back on the same cadence; `visibilitychange` also wakes us, so
        // this is only the fallback for browsers that fire it unreliably.
        timer = window.setTimeout(tick, every);
        return;
      }

      controller = new AbortController();
      try {
        const data = await api.latest(symbol, interval, controller.signal);
        if (stopped) return;
        failures.current = 0;
        setState({ candles: data.candles, streaming: true });
      } catch {
        if (stopped) return;
        // Keep the last good bars on screen: a dropped poll is not a reason to
        // blank a chart that is still perfectly readable.
        failures.current += 1;
        setState((prev) => ({ ...prev, streaming: false }));
      } finally {
        controller = null;
      }

      if (stopped) return;
      // Back off after repeated failures so a backend that is down is not
      // polled every 5 seconds by every open tab. Capped at ~1 minute.
      const delay = Math.min(every * 2 ** Math.min(failures.current, 4), 60000);
      timer = window.setTimeout(tick, delay);
    };

    const onVisible = () => {
      if (document.visibilityState !== "visible" || stopped) return;
      // Coming back to the tab should refresh at once rather than waiting out
      // the remainder of a timer that has been throttled in the background.
      window.clearTimeout(timer);
      void tick();
    };

    document.addEventListener("visibilitychange", onVisible);
    void tick();

    return () => {
      stopped = true;
      window.clearTimeout(timer);
      controller?.abort();
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [symbol, interval, every, enabled]);

  return state;
}
