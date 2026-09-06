import { createContext, useContext } from "react";
import { dictionaries, en, type Locale, type StringKey } from "./dictionary";

export type Translate = (key: StringKey) => string;

interface I18nValue {
  locale: Locale;
  t: Translate;
  toggleLocale: () => void;
}

/**
 * Context rather than a plain hook: every panel needs `t`, and threading it
 * through props would put a translation argument on components that otherwise
 * take only data.
 */
export const I18nContext = createContext<I18nValue>({
  locale: "en",
  t: (key) => en[key],
  toggleLocale: () => {},
});

export function useI18n(): I18nValue {
  return useContext(I18nContext);
}

export function translator(locale: Locale): Translate {
  const dictionary = dictionaries[locale];
  // Falling back to English rather than rendering the raw key: a missing string
  // should degrade to a readable label, not to `regime.hurstHint`. The typed
  // dictionary makes this unreachable in practice.
  return (key) => dictionary[key] ?? en[key];
}
