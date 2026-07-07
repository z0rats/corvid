import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enCommon from './locales/en/common.json';
import ruCommon from './locales/ru/common.json';
import enSettings from './locales/en/settings.json';
import ruSettings from './locales/ru/settings.json';
import enCvssCalculator from './locales/en/cvssCalculator.json';
import ruCvssCalculator from './locales/ru/cvssCalculator.json';
import enEmailAnalyzer from './locales/en/emailAnalyzer.json';
import ruEmailAnalyzer from './locales/ru/emailAnalyzer.json';
import enImageTools from './locales/en/imageTools.json';
import ruImageTools from './locales/ru/imageTools.json';
import enIocTools from './locales/en/iocTools.json';
import ruIocTools from './locales/ru/iocTools.json';
import enLlmTemplates from './locales/en/llmTemplates.json';
import ruLlmTemplates from './locales/ru/llmTemplates.json';
import enNewsfeed from './locales/en/newsfeed.json';
import ruNewsfeed from './locales/ru/newsfeed.json';
import enRuleCreator from './locales/en/ruleCreator.json';
import ruRuleCreator from './locales/ru/ruleCreator.json';
import enUsernameSearch from './locales/en/usernameSearch.json';
import ruUsernameSearch from './locales/ru/usernameSearch.json';
import enEmailSearch from './locales/en/emailSearch.json';
import ruEmailSearch from './locales/ru/emailSearch.json';

export const SUPPORTED_LANGUAGES = ['en', 'ru'];
export const DEFAULT_LANGUAGE = 'en';

export const NAMESPACES = [
  'common',
  'settings',
  'cvssCalculator',
  'emailAnalyzer',
  'imageTools',
  'iocTools',
  'llmTemplates',
  'newsfeed',
  'ruleCreator',
  'usernameSearch',
  'emailSearch',
];

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        common: enCommon,
        settings: enSettings,
        cvssCalculator: enCvssCalculator,
        emailAnalyzer: enEmailAnalyzer,
        imageTools: enImageTools,
        iocTools: enIocTools,
        llmTemplates: enLlmTemplates,
        newsfeed: enNewsfeed,
        ruleCreator: enRuleCreator,
        usernameSearch: enUsernameSearch,
        emailSearch: enEmailSearch,
      },
      ru: {
        common: ruCommon,
        settings: ruSettings,
        cvssCalculator: ruCvssCalculator,
        emailAnalyzer: ruEmailAnalyzer,
        imageTools: ruImageTools,
        iocTools: ruIocTools,
        llmTemplates: ruLlmTemplates,
        newsfeed: ruNewsfeed,
        ruleCreator: ruRuleCreator,
        usernameSearch: ruUsernameSearch,
        emailSearch: ruEmailSearch,
      },
    },
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
