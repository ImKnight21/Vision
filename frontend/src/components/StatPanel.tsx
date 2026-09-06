import type { ReactNode } from "react";
import "./StatPanel.css";

export interface StatItem {
  label: string;
  value: string;
  /** Colour class from `signClass`, or a fixed tone. */
  tone?: string;
  /** Plain-language explanation, surfaced on hover and to screen readers. */
  hint?: string;
}

interface Props {
  title: string;
  note?: string;
  items: StatItem[];
  children?: ReactNode;
}

export function StatPanel({ title, note, items, children }: Props) {
  return (
    <section className="stat panel panel--bracketed">
      <div className="panel__title">
        <span>{title}</span>
        {note && <span className="stat__note">{note}</span>}
      </div>

      <dl className="stat__list">
        {items.map((item) => (
          <div className="stat__row" key={item.label} title={item.hint}>
            <dt className="stat__label">
              {item.label}
              {item.hint && <span className="visually-hidden"> — {item.hint}</span>}
            </dt>
            {/* The leader is decorative: it guides the eye across the gap the
                way a printed table of contents does. */}
            <span className="stat__leader" aria-hidden="true" />
            <dd className={`stat__value ${item.tone ?? ""}`}>{item.value}</dd>
          </div>
        ))}
      </dl>

      {children}
    </section>
  );
}
