import type { Comparison, IntervalOption, MarketRow, Overview } from "./types";

/** In dev the Vite proxy serves /api; in production set VITE_API_BASE_URL. */
const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, { signal, headers: { Accept: "application/json" } });
  } catch (cause) {
    // An aborted request is a normal part of switching coins, not a failure.
    if (signal?.aborted) throw cause;
    throw new ApiError("Cannot reach the Vision API. Is the backend running?", 0);
  }

  if (!response.ok) {
    // FastAPI puts the reason in `detail`; fall back to the status text.
    const detail = await response
      .json()
      .then((body) => (typeof body?.detail === "string" ? body.detail : null))
      .catch(() => null);
    throw new ApiError(detail ?? `Request failed (${response.status})`, response.status);
  }

  return response.json() as Promise<T>;
}

export const api = {
  markets: (limit = 120, signal?: AbortSignal) =>
    request<{ count: number; markets: MarketRow[] }>(`/api/markets?limit=${limit}`, signal),

  overview: (symbol: string, interval: string, limit = 500, signal?: AbortSignal) =>
    request<Overview>(
      `/api/overview/${encodeURIComponent(symbol)}?interval=${interval}&limit=${limit}`,
      signal,
    ),

  compare: (symbols: string[], interval: string, limit = 500, signal?: AbortSignal) =>
    request<Comparison>(
      `/api/compare?symbols=${encodeURIComponent(symbols.join(","))}` +
        `&interval=${interval}&limit=${limit}`,
      signal,
    ),

  intervals: (signal?: AbortSignal) =>
    request<{ intervals: IntervalOption[] }>("/api/intervals", signal),
};
