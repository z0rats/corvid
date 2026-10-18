import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Every locales/<lang>/<namespace>.json is a namespace named after its file, so a new feature's
// strings need no registration here. `ru` is intentionally partial; missing keys fall back to `en`.
const loadLocale = (modules) =>
  Object.fromEntries(
    Object.entries(modules).map(([file, mod]) => [file.match(/\/([^/]+)\.json$/)[1], mod.default ?? mod])
  );

const en = loadLocale(import.meta.glob('./locales/en/*.json', { eager: true }));
const ru = loadLocale(import.meta.glob('./locales/ru/*.json', { eager: true }));

export const SUPPORTED_LANGUAGES = ['en', 'ru'];
export const DEFAULT_LANGUAGE = 'en';

export const NAMESPACES = Object.keys(en);

// First-paint language until the server-side setting arrives (useAppSettings): the last language
// used in this browser, else the browser's own preference. Storage can throw (private mode).
const LANGUAGE_STORAGE_KEY = 'i18nextLng';

const readStoredLanguage = () => {
  try {
    return localStorage.getItem(LANGUAGE_STORAGE_KEY);
  } catch {
    return null;
  }
};

export const detectInitialLanguage = (stored, browserLanguages) =>
  [stored, ...browserLanguages]
    .map((lang) => lang?.toLowerCase().split('-')[0])
    .find((lang) => SUPPORTED_LANGUAGES.includes(lang)) ?? DEFAULT_LANGUAGE;

i18n.on('languageChanged', (lang) => {
  try {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
  } catch {
    // Not persisted; the server-side setting still applies on next load.
  }
});

i18n
  .use(initReactI18next)
  .init({
    resources: { en, ru },
    lng: detectInitialLanguage(readStoredLanguage(), navigator.languages ?? [navigator.language]),
    fallbackLng: DEFAULT_LANGUAGE,
    supportedLngs: SUPPORTED_LANGUAGES,
    defaultNS: 'common',
    ns: NAMESPACES,
    interpolation: { escapeValue: false },
  });

export default i18n;
