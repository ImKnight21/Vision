# Design system

The reference is a monochrome phosphor terminal from a 1980s trading desk —
the machine a dealer actually read numbers off, not a retro-styled poster of
one. That distinction drives every decision below: the aesthetic is allowed to
be decorative only where it does not cost legibility, because the screen's job
is dense numeric data.

## Principles

1. **One typeface, monospace, tabular figures.** Prices sit in columns and must
   not shift as digits change. `font-variant-numeric: tabular-nums` is set
   globally.
2. **Colour carries meaning or is absent.** The interface is one phosphor hue
   plus up/down. There is no decorative palette.
3. **No rounded corners, no shadows-as-depth.** `--radius: 0`. Panels are
   separated by 1px rules and corner brackets, the way a character-cell display
   drew boxes.
4. **Density over whitespace.** The spacing scale is deliberately tight. A
   terminal that shows twelve statistics without scrolling beats one that shows
   four beautifully.
5. **Effects yield to preference.** Scanlines dim and animation stops under
   `prefers-reduced-motion`.

## Tokens

All tokens live in [`frontend/src/styles/tokens.css`](../frontend/src/styles/tokens.css).
Components reference tokens only — no component hard-codes a colour.

### The tube

Two phosphor types, switched by `data-phosphor` on `<html>` and remembered in
`localStorage`:

| | P1 (green, default) | P3 (amber) |
| --- | --- | --- |
| `--phosphor` | `#3dff7a` | `#ffb340` |
| `--bg` | `#040604` | `#060402` |
| `--text` | `#b7f5c8` | `#f5d9a8` |

Because the amber tube redefines every colour token rather than filtering the
page, `--up` and `--down` stay distinguishable in both: they differ in
brightness as well as hue, so the distinction survives for a viewer who cannot
separate the hues.

### Type scale

Fluid, `clamp()`-based, from `--step--1` (labels) to `--step-3` (the one large
number on the screen: the price). IBM Plex Mono, with a real monospace fallback
stack so the layout holds if Google Fonts is unreachable.

### Spacing

`--space-1` (0.25rem) through `--space-6` (2.25rem). Most panel padding is
`--space-2` or `--space-3`.

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

## Extending it

When adding a panel: use `.panel panel--bracketed`, give it a `.panel__title`,
and build rows with `StatPanel` rather than a bespoke table. If a statistic
needs a visual, reach for `Meter` before inventing a new chart — the terminal's
consistency is worth more than a locally optimal widget.
