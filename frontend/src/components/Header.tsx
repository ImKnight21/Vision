import { useClock } from "../hooks/useClock";
import type { Phosphor } from "../hooks/usePhosphor";
import "./Header.css";

interface Props {
  phosphor: Phosphor;
  onTogglePhosphor: () => void;
  onOpenMarkets: () => void;
  status: "live" | "loading" | "error";
}

const STATUS_LABEL: Record<Props["status"], string> = {
  live: "ONLINE",
  loading: "SYNC",
  error: "NO LINK",
};

export function Header({ phosphor, onTogglePhosphor, onOpenMarkets, status }: Props) {
  const clock = useClock();

  return (
    <header className="header">
      <div className="header__brand">
        <span className="header__logo" aria-hidden="true">
          ▚▞
        </span>
        <h1 className="header__title">VISION</h1>
        <span className="header__subtitle">MARKET TERMINAL</span>
      </div>

      <div className="header__controls">
        <button
          type="button"
          className="header__button header__button--markets"
          onClick={onOpenMarkets}
        >
          [ MARKETS ]
        </button>

        <button
          type="button"
          className="header__button"
          onClick={onTogglePhosphor}
          aria-label={`Switch to ${phosphor === "green" ? "amber" : "green"} phosphor`}
        >
          TUBE:{phosphor === "green" ? "P1" : "P3"}
        </button>

        <span className={`header__status header__status--${status}`}>
          <span className="header__dot" aria-hidden="true" />
          {STATUS_LABEL[status]}
        </span>

        <time className="header__clock" dateTime={clock}>
          {clock}
          <span className="blink" aria-hidden="true">
            Z
          </span>
        </time>
      </div>
    </header>
  );
}
