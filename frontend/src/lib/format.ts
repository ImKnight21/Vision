/** Display helpers. Every function tolerates null so panels can render
 *  a placeholder rather than crashing on a statistic we could not compute. */

// Two hyphens, not an em dash: the dash characters render inconsistently in a
// monospace column and the design system bans them outright.
const DASH = "--";

/** Crypto prices span nine orders of magnitude, so precision has to adapt. */
export function price(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return DASH;
  const abs = Math.abs(value);
  const decimals = abs >= 1000 ? 2 : abs >= 1 ? 2 : abs >= 0.01 ? 4 : abs >= 0.0001 ? 6 : 8;
  return value.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/** A fraction rendered as a signed percent: 0.0241 -> "+2.41%". */
export function percent(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return DASH;
  return `${value >= 0 ? "+" : "−"}${Math.abs(value * 100).toFixed(digits)}%`;
}

/** An unsigned percent, for magnitudes where the sign carries no meaning. */
export function magnitude(value: number | null | undefined, digits = 1): string {
  if (value == null || !Number.isFinite(value)) return DASH;
  return `${(value * 100).toFixed(digits)}%`;
}

export function ratio(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return DASH;
  return value.toFixed(digits);
}

/** Large sums in terminal shorthand: 1.24B, 890.5M. */
export function compact(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return DASH;
  const abs = Math.abs(value);
  const [scale, suffix] =
    abs >= 1e12 ? [1e12, "T"] :
    abs >= 1e9 ? [1e9, "B"] :
    abs >= 1e6 ? [1e6, "M"] :
    abs >= 1e3 ? [1e3, "K"] :
    [1, ""];
  return `${(value / scale!).toFixed(abs >= 1e3 ? 2 : 0)}${suffix}`;
}

export function shortDate(iso: string | null | undefined): string {
  if (!iso) return DASH;
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? DASH
    : date.toISOString().slice(0, 10).replace(/-/g, ".");
}

export function integer(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return DASH;
  return Math.round(value).toLocaleString("en-US");
}

/** Class name that colours a value by its sign. */
export function signClass(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value) || value === 0) return "value-flat";
  return value > 0 ? "value-up" : "value-down";
}

export { DASH };
