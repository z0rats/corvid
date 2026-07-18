# i18n pattern for batch-translating features

Reference this file when spawning subagents to add/extend translations for a feature, instead
of repeating this pattern in every subagent's prompt. Pass only the feature-specific scope
(namespace, files in scope, output dir) — the subagent should read this file itself.

## Where things live

- Locale files: `src/core/i18n/locales/<lang>/<namespace>.json` — currently `en` and `ru`.
- Namespace registry: `src/core/i18n/index.js` — `NAMESPACES` array + the `resources` object in
  `i18n.init()`. Adding a **new** namespace means importing both locale JSONs there and adding
  the key to `NAMESPACES`. Adding keys to an **existing** namespace does not touch this file.
- Existing namespaces: `common`, `settings`, `cvssCalculator`, `emailAnalyzer`, `imageTools`,
  `iocTools`, `llmTemplates`, `newsfeed`, `ruleCreator`, `usernameSearch`, `emailSearch`,
  `redditSearch`.

## Code pattern (reference file: `src/features/username-search/components/NewSearch.jsx`)

```jsx
import { useTranslation } from 'react-i18next';

export default function SomeComponent() {
  const { t } = useTranslation('usernameSearch'); // <- the feature's namespace
  return <Typography>{t('page.title')}</Typography>;
}
```

- One `useTranslation('<namespace>')` call per component, at the top.
- Keys are dot-nested (`page.title`, `form.submitLabel`, etc.) — group by screen/section within
  the namespace JSON, mirroring the component tree where practical.
- Both `en/<namespace>.json` and `ru/<namespace>.json` must get the same keys added in the same
  PR/commit — a missing key in one locale doesn't error, it just silently shows nothing (no
  fallback-to-English), so always add both.

## 6 rules: translate vs. don't

1. **Translate**: user-facing labels, button text, headings, placeholders, tooltips, empty-state
   copy, error/success messages shown in the UI.
2. **Translate**: dynamic strings built from translated fragments (e.g. `t('foundCount', { count })`
   using i18next interpolation) — don't hardcode pluralization/interpolation in JS string
   concatenation.
3. **Don't translate**: internal identifiers, API field names, enum/constant values used for
   logic (e.g. a `status === 'pending'` check), CSS class names, test IDs.
4. **Don't translate**: brand/proper nouns (station names, service names like "VirusTotal",
   "Shodan", "Maigret") or anything already established as untranslated elsewhere in the app
   (mirrors the `app_name`-stays-untranslated convention documented for this project).
5. **Don't translate**: log messages, console output, code comments — these are developer-facing
   only.
6. **Translate but verify placeholders survive**: when a string carries `{{variable}}`
   interpolation or pluralization, make sure the translated Russian string keeps the same
   `{{variable}}` placeholders (same names, same count) — i18next won't error on a missing one,
   it just renders blank.

## Deliverable format

For each feature translated, report:

- Which namespace(s) touched (existing, or newly added — and if newly added, confirm
  `src/core/i18n/index.js` was updated).
- List of new/changed keys, grouped by JSON file (`en/<ns>.json`, `ru/<ns>.json`).
- List of component files updated to use `useTranslation`/`t(...)`.
- Any strings intentionally left untranslated and why (rule 3/4/5 above).
- Confirm both locale files have identical key sets after the change (no orphaned/missing keys).

## For subagent prompts

When spawning a subagent to translate a feature, its prompt only needs:

```
Add/extend i18n for <feature name> per frontend/I18N_PATTERN.md (read it yourself for the
full pattern, rules, and deliverable format).
Scope: <files/components in scope>
Namespace: <existing namespace name, or "new: <name>" if it needs to be created>
Output: report per the deliverable format in I18N_PATTERN.md
```

Do not paste the code pattern, the 6 rules, or the deliverable format into the subagent's
prompt directly — that's what blew up token usage in the original batch-translation session (the same ~470-word boilerplate repeated verbatim across ~10 subagent prompts). Point at this file instead.
