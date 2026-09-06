import { useCallback, useEffect, useRef, useState } from "react";

interface AsyncState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
  /**
   * Still loading past `slowAfterMs`. Free hosting sleeps after inactivity and
   * takes the better part of a minute to wake, which is indistinguishable from
   * a hang unless the interface says so.
   */
  slow: boolean;
}

interface Options {
  keepPrevious?: boolean;
  slowAfterMs?: number;
}

/**
 * Runs an aborting async function and tracks its state.
 *
 * The previous request is aborted whenever `deps` change, so rapidly switching
 * coins cannot leave a slow earlier response to overwrite the current one.
 */
export function useAsync<T>(
  fn: (signal: AbortSignal) => Promise<T>,
  deps: unknown[],
  { keepPrevious = false, slowAfterMs = 4000 }: Options = {},
): AsyncState<T> & { reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: null,
    loading: true,
    slow: false,
  });
  const [nonce, setNonce] = useState(0);

  // Keeping the callback in a ref lets `deps` stay the caller's own list
  // instead of forcing them to memoise the function too.
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    const controller = new AbortController();
    setState((prev) => ({
      data: keepPrevious ? prev.data : null,
      error: null,
      loading: true,
      slow: false,
    }));

    const slowTimer = window.setTimeout(() => {
      if (!controller.signal.aborted) {
        setState((prev) => (prev.loading ? { ...prev, slow: true } : prev));
      }
    }, slowAfterMs);

    fnRef
      .current(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) {
          setState({ data, error: null, loading: false, slow: false });
        }
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          data: null,
          error: error instanceof Error ? error : new Error(String(error)),
          loading: false,
          slow: false,
        });
      })
      .finally(() => window.clearTimeout(slowTimer));

    return () => {
      window.clearTimeout(slowTimer);
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { ...state, reload };
}
