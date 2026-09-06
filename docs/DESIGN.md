# Design system

The reference is a monochrome phosphor terminal from a 1980s trading desk —
the machine a dealer actually read numbers off, not a retro-styled poster of
one. That distinction drives every decision below: the aesthetic is allowed to
be decorative only where it does not cost legibility, because the screen's job
is dense numeric data.

## Principles

1. **One typeface, monospace, tabular figures.** Prices sit in columns and must
   not shift as digits change, and `0` must never be mistaken for `O`:
   `font-variant-numeric: tabular-nums slashed-zero` is set globally.
2. **Colour carries meaning or is absent.** The interface is one phosphor hue
   plus up/down. There is no decorative palette.
3. **No rounded corners, no shadows-as-depth.** `--radius: 0`. Panels are
   separated by 1px rules and corner brackets, the way a character-cell display
   drew boxes.
4. **Density over whitespace.** The spacing scale is deliberately tight. A
   terminal that shows twelve statistics without scrolling beats one that shows
   four beautifully.
5. **Effects yield to preference.** Scanlines dim and animation stops under
   `prefers-reduced-motion`, and `FX:OFF` retracts the tube effects entirely.
   No amount of atmosphere is worth a number the reader cannot trust.

## Tokens

All tokens live in [`frontend/src/styles/tokens.css`](../frontend/src/styles/tokens.css).
Components reference tokens only — no component hard-codes a colour.

### The tube

Two phosphor types, switched by `data-phosphor` on `<html>` and remembered in
`localStorage`:

| | P1 (green, default) | P3 (amber) |
| --- | --- | --- |
| `--phosphor` | `#4dff85` | `#ffc154` |
| `--bg-panel` | `#070c08` | `#0c0805` |
| `--text` | `#ccffd9` | `#ffe6bd` |
| `--text-dim` | `#8fd6a4` | `#dbae74` |
| `--text-faint` | `#6aae7f` | `#b78a55` |

Because the amber tube redefines every colour token rather than filtering the
page, `--up` and `--down` stay distinguishable in both: they differ in
brightness as well as hue, so the distinction survives for a viewer who cannot
separate the hues.

### Type scale

Fluid, `clamp()`-based, from `--step--1` (labels) to `--step-3` (the one large
number on the screen: the price). JetBrains Mono, falling back to IBM Plex Mono
and then a real system monospace stack, so the layout holds if Google Fonts is
unreachable. See [Legibility](#legibility) for why that face.

### Spacing

`--space-1` (0.25rem) through `--space-6` (2.25rem). Most panel padding is
`--space-2` or `--space-3`.

## Legibility

The aesthetic is subordinate to reading numbers. Three things enforce that.

**Measured contrast, not eyeballed.** Every text token clears WCAG AA against
its own background *after* the scanline overlay darkens both — the overlay is
part of the design, so it has to be part of the measurement. The first pass got
this wrong: `--text-faint` sat at 2.21:1 raw and 1.52:1 through scanlines, and
it was carrying coin names, ranks and volumes.

| Token | Before | Now (raw) | Now (through scanlines) |
| ----- | ------ | --------- | ----------------------- |
| `--text` | 15.87 | 17.72 | 12.97 |
| `--text-dim` | 4.98 | 11.57 | 8.62 |
| `--text-faint` | **2.21** | 7.49 | 5.72 |

Decoration was split off into `--rule` and `--rule-faint` at the same time, so
raising text contrast did not turn hairlines and dotted leaders into shouting.

**A typeface chosen for disambiguation.** JetBrains Mono, with
`font-variant-numeric: tabular-nums slashed-zero`. It draws `0`/`O` and
`1`/`l`/`I` as unmistakably different shapes, which is exactly the failure mode
of a dense price table. Base size is ~15px, not the ~13.5px the first pass used.

**The glass is optional.** `FX:ON/OFF` in the header retracts scanlines,
vignette and glow via `data-fx="off"`. It changes no colour, so contrast only
improves. Scanlines default to 0.14 opacity on a 5px period; the original 0.35
on a 4px period cut every contrast ratio by roughly half.

Glow is capped at a few pixels of blur throughout. Past that it eats the edges
of the glyphs it is meant to flatter — which is why the headline price is
`--phosphor-bright` with a soft glow rather than a hard one, and why it is no
longer tinted by direction: colouring the largest element on screen alarm-red
over a −0.02% move was noise, not signal.

## Components

| Piece | Note |
| ----- | ---- |
| `.panel` | The base surface: panel background, 1px rule. |
| `.panel--bracketed` | Adds corner brackets via `::before`/`::after` — no extra markup. |
| `.panel__title` | Uppercase, letter-spaced, on a faint phosphor wash. |
| `StatPanel` | Label / dotted leader / value rows. The leader guides the eye across the gap the way a printed table of contents does. |
| `Meter` | A hatched track with a glowing cursor, for RSI, drawdown depth and position-in-range. |
| `PriceChart` | lightweight-charts, reading its palette from the CSS tokens at mount so it follows the tube switch. |

## Responsiveness

Two structural breakpoints, and as few as possible:

- **≥ 961px** — two columns: a fixed market list beside the detail view.
- **≤ 960px** — the sidebar becomes a drawer opened from `[ MARKETS ]` in the
  header. Escape and the scrim both close it; selecting a coin closes it too.
- **≤ 720px** — the header sheds its subtitle and status pill.
- **≤ 560px** — control chips scroll horizontally rather than wrapping into
  ragged rows.

The statistics grid needs no breakpoint at all: `repeat(auto-fit, minmax(17rem,
1fr))` reflows it from four columns to one on its own.

## Traps found while building this

- **`overflow: hidden` collapses a flex item.** It zeroes the automatic minimum
  size, so inside a scrolling flex column the chart panel shrank to its 2px
  borders. Fixed with `flex-shrink: 0` on `.app__main > *`.
- **Chart axis dates follow the viewer's system locale** unless
  `localization.locale` is pinned, which left English labels sitting next to
  Russian month abbreviations.
- **`localStorage` throws, not just returns null**, in private windows and when
  site data is blocked. Every access is wrapped.
- **A child's effects run before its parent's.** The theme hook set
  `data-phosphor` in an effect, so when the tube was switched the chart — a
  child that re-reads its palette from the CSS variables — sampled the *previous*
  theme and stayed green on an amber screen. The attribute is now written
  synchronously in the toggle handler, before React re-renders.

## Extending it

When adding a panel: use `.panel panel--bracketed`, give it a `.panel__title`,
and build rows with `StatPanel` rather than a bespoke table. If a statistic
needs a visual, reach for `Meter` before inventing a new chart — the terminal's
consistency is worth more than a locally optimal widget.
