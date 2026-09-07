import { dictionaries, type Locale, type StringKey } from "./dictionary";
import { useI18n } from "./useI18n";
import "./Stable.css";

const LOCALES = Object.keys(dictionaries) as Locale[];

interface Props {
  /** The string to display. */
  show: StringKey;
  /**
   * Every string this slot may hold. Defaults to `show` alone; pass the whole
   * set when the text also changes for reasons other than language, such as a
   * status that cycles between "online", "loading" and "error".
   */
  among?: readonly StringKey[];
  className?: string;
  /** Where the visible text sits inside the reserved box. */
  align?: "start" | "center" | "end";
}

/**
 * Reserves the width of the widest translation, so the layout does not move
 * when the language changes.
 *
 * Every variant is rendered into the same grid cell and all but one is hidden.
 * A grid cell is as wide as its widest child, so the box is the width of the
 * longest string in any locale whether or not that locale is showing. The
 * alternative -- a hand-written `min-width` per control -- has to be re-measured
 * by a person every time a translation changes, and silently stops being true
 * when nobody does.
 *
 * Measured before this existed: switching to English moved the header controls
 * by up to 93px, because "ЭФФЕКТЫ:ON" is 47px wider than "FX:ON" and every
 * control to its left slid along.
 *
 * `visibility: hidden` rather than `display: none`, because a hidden grid item
 * still occupies its cell; it is also skipped by screen readers, so only the
 * visible string is announced.
 */
export function Stable({ show, among, className, align = "start" }: Props) {
  const { locale } = useI18n();
  const keys = among ?? [show];

  return (
    <span className={`stable${className ? ` ${className}` : ""}`} data-align={align}>
      {LOCALES.map((candidate) =>
        keys.map((key) => {
          const active = candidate === locale && key === show;
          return (
            <span
              key={`${candidate}:${key}`}
              className="stable__variant"
              data-active={active || undefined}
            >
              {dictionaries[candidate][key]}
            </span>
          );
        }),
      )}
    </span>
  );
}
