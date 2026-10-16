import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

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

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en, ru },
    fallbackLng: DEFAULT_LANGUAGE,
    supportedLngs: SUPPORTED_LANGUAGES,
    defaultNS: 'common',
    ns: NAMESPACES,
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export default i18n;
