#!/usr/bin/env node
/**
 * Fails if any locale JSON file under src/core/i18n/locales/<lang>/ has a
 * different set of (nested) keys than its counterpart in another locale.
 * Catches a new feature's translation keys silently shipping English-only.
 */
const fs = require('fs');
const path = require('path');

const LOCALES_DIR = path.join(__dirname, '..', 'src', 'core', 'i18n', 'locales');
const LANGUAGES = fs.readdirSync(LOCALES_DIR).filter((entry) =>
  fs.statSync(path.join(LOCALES_DIR, entry)).isDirectory()
);

function collectKeys(obj, prefix = '') {
  return Object.entries(obj).flatMap(([key, value]) => {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return collectKeys(value, fullKey);
    }
    return [fullKey];
  });
}

function main() {
  if (LANGUAGES.length < 2) {
    console.log('i18n key check: fewer than 2 locales found, nothing to compare.');
    return;
  }

  const [baseLang, ...otherLangs] = LANGUAGES;
  const baseDir = path.join(LOCALES_DIR, baseLang);
  const namespaceFiles = fs.readdirSync(baseDir).filter((f) => f.endsWith('.json'));

  let hasMismatch = false;

  for (const file of namespaceFiles) {
    const baseKeys = new Set(collectKeys(JSON.parse(fs.readFileSync(path.join(baseDir, file), 'utf8'))));

    for (const lang of otherLangs) {
      const langFile = path.join(LOCALES_DIR, lang, file);
      if (!fs.existsSync(langFile)) {
        console.error(`[i18n] ${file}: missing entirely for locale "${lang}"`);
        hasMismatch = true;
        continue;
      }

      const langKeys = new Set(collectKeys(JSON.parse(fs.readFileSync(langFile, 'utf8'))));
      const missingInLang = [...baseKeys].filter((k) => !langKeys.has(k));
      const extraInLang = [...langKeys].filter((k) => !baseKeys.has(k));

      if (missingInLang.length || extraInLang.length) {
        hasMismatch = true;
        console.error(`[i18n] ${file}: "${baseLang}" vs "${lang}" mismatch`);
        if (missingInLang.length) console.error(`  missing in ${lang}: ${missingInLang.join(', ')}`);
        if (extraInLang.length) console.error(`  extra in ${lang} (not in ${baseLang}): ${extraInLang.join(', ')}`);
      }
    }
  }

  if (hasMismatch) {
    console.error('\ni18n key check failed: locale files are out of sync.');
    process.exit(1);
  }

  console.log(`i18n key check passed: ${namespaceFiles.length} namespace(s) in sync across [${LANGUAGES.join(', ')}].`);
}

main();
