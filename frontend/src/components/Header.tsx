import { useClock } from "../hooks/useClock";
import type { Fx, Phosphor } from "../hooks/useDisplay";
import { useI18n } from "../i18n/useI18n";
import type { StringKey } from "../i18n/dictionary";
import "./Header.css";

interface Props {
  phosphor: Phosphor;
  onTogglePhosphor: () => void;
  fx: Fx;
  onToggleFx: () => void;
  onOpenMarkets: () => void;
  onOpenCompare: () => void;
  compareOpen: boolean;
  status: "live" | "loading" | "error";
}

const STATUS_KEY: Record<Props["status"], StringKey> = {
  live: "status.live",
  loading: "status.loading",
  error: "status.error",
};

export function Header({
  phosphor,
  onTogglePhosphor,
  fx,
  onToggleFx,
  onOpenMarkets,
  onOpenCompare,
  compareOpen,
  status,
}: Props) {
  const clock = useClock();
  const { t, locale, toggleLocale } = useI18n();

  return (
    <header className="header">
      <div className="header__brand">
        <span className="header__logo" aria-hidden="true">
          ▚▞
        </span>
        <h1 className="header__title">VISION</h1>
        <span className="header__subtitle">{t("brand.subtitle")}</span>
      </div>

      <div className="header__controls">
        <button
          type="button"
          className="header__button header__button--markets"
          onClick={onOpenMarkets}
        >
          {t("header.markets")}
        </button>

        <button
          type="button"
          className={`header__button${compareOpen ? " header__button--on" : ""}`}
          onClick={onOpenCompare}
          aria-pressed={compareOpen}
        >
          {compareOpen ? t("compare.close") : t("compare.open")}
        </button>

        <button
          type="button"
          className="header__button"
          onClick={toggleLocale}
          title={t("header.langHint")}
        >
          <span className="header__key">{t("header.lang")}:</span>
          {locale.toUpperCase()}
        </button>

        <button
          type="button"
          className="header__button"
          onClick={onTogglePhosphor}
          aria-label={`Switch to ${phosphor === "green" ? "amber" : "green"} phosphor`}
        >
          <span className="header__key">{t("header.tube")}:</span>
          {phosphor === "green" ? "P1" : "P3"}
        </button>

        <button
          type="button"
          className="header__button"
          onClick={onToggleFx}
          aria-pressed={fx === "on"}
          title={t("header.fxHint")}
        >
          <span className="header__key">{t("header.fx")}:</span>
          {fx.toUpperCase()}
        </button>

        <span className={`header__status header__status--${status}`}>
          <span className="header__dot" aria-hidden="true" />
          {t(STATUS_KEY[status])}
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
