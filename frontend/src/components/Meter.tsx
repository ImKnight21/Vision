import { Hint } from "./Hint";
import "./Meter.css";

interface Props {
  label: string;
  /** Where the marker sits, 0..1. Null renders an empty track. */
  position: number | null;
  leftLabel: string;
  rightLabel: string;
  hint?: string;
  /** Optional bands drawn on the track, e.g. RSI's 30/70 lines. */
  marks?: number[];
}

export function Meter({ label, position, leftLabel, rightLabel, hint, marks = [] }: Props) {
  const clamped = position == null ? null : Math.min(1, Math.max(0, position));

  return (
    <div className="meter">
      <div className="meter__head">
        <span className="meter__label">
          {hint ? <Hint term={label} text={hint} /> : label}
        </span>
        <span className="meter__readout">
          {clamped == null ? "--" : `${(clamped * 100).toFixed(0)}%`}
        </span>
      </div>

      <div
        className="meter__track"
        role="meter"
        aria-label={label}
        aria-valuenow={clamped ?? undefined}
        aria-valuemin={0}
        aria-valuemax={1}
      >
        {marks.map((mark) => (
          <span
            key={mark}
            className="meter__mark"
            style={{ left: `${mark * 100}%` }}
            aria-hidden="true"
          />
        ))}
        {clamped != null && (
          <>
            <span className="meter__fill" style={{ width: `${clamped * 100}%` }} />
            <span className="meter__cursor" style={{ left: `${clamped * 100}%` }} />
          </>
        )}
      </div>

      <div className="meter__scale">
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
    </div>
  );
}
