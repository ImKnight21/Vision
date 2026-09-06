import { useCallback, useEffect, useRef, useState } from "react";

export type Phosphor = "green" | "amber";
export type Fx = "on" | "off";

/**
 * A setting persisted per browser and mirrored onto <html> as a data attribute,
 * so the CSS can switch on it without any component re-rendering.
 *
 * Every storage access is wrapped: private windows and blocked site data make
 * `localStorage` *throw*, not merely return null.
 */
function usePersistedAttribute<T extends string>(
  key: string,
  attribute: string,
  values: readonly [T, T],
): [T, () => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const stored = localStorage.getItem(key);
      return values.includes(stored as T) ? (stored as T) : values[0];
    } catch {
      return values[0];
    }
  });

  useEffect(() => {
    document.documentElement.setAttribute(attribute, value);
    try {
      localStorage.setItem(key, value);
    } catch {
      // A remembered preference is a convenience; losing it is not an error.
    }
  }, [attribute, key, value]);

  const latest = useRef(value);
  latest.current = value;

  const toggle = useCallback(() => {
    const next = latest.current === values[0] ? values[1] : values[0];
    // Write the attribute here, in the event handler, rather than leaving it to
    // the effect above. React runs a child's effects before its parent's, so
    // the chart — which re-reads its palette from these CSS variables — would
    // otherwise sample the *previous* theme and stay green on an amber tube.
    document.documentElement.setAttribute(attribute, next);
    setValue(next);
    // `values` is a literal tuple at every call site, so it is stable in practice.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attribute]);

  return [value, toggle];
}

/** Which phosphor the tube is running. */
export function usePhosphor(): [Phosphor, () => void] {
  return usePersistedAttribute<Phosphor>("vision.phosphor", "data-phosphor", [
    "green",
    "amber",
  ]);
}

/**
 * Whether the tube's glass effects are drawn at all.
 *
 * Scanlines, vignette and glow are the part of the aesthetic that costs
 * legibility, so they are a setting rather than a fixture. Turning them off
 * changes no colour — contrast can only improve.
 */
export function useCrtEffects(): [Fx, () => void] {
  return usePersistedAttribute<Fx>("vision.fx", "data-fx", ["on", "off"]);
}
