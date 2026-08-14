import { createRequire } from 'node:module';
import js from '@eslint/js';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import globals from 'globals';
import tseslint from 'typescript-eslint';

// `settings.react.version: 'detect'` calls eslint-plugin-react's own
// auto-detection, which relies on the RuleContext#getFilename() method
// ESLint 10 removed (react/display-name crashes on every file otherwise).
// Reading the installed version ourselves sidesteps that broken codepath
// until eslint-plugin-react ships an ESLint-10-compatible release.
const { version: reactVersion } = createRequire(import.meta.url)('react/package.json');

export default [
  { ignores: ['build/**', 'node_modules/**', 'coverage/**'] },
  { settings: { react: { version: reactVersion } } },
  js.configs.recommended,
  react.configs.flat.recommended,
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ...react.configs.flat.recommended.languageOptions,
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      // Only the two classic hooks rules (CRA's eslint-config-react-app parity) -
      // v7's "recommended" also bundles React Compiler-readiness rules
      // (set-state-in-effect, refs, purity, ...) that would flag a wave of
      // pre-existing, unrelated patterns out of scope for a build-tool migration.
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      'react/prop-types': 'off',
      'react/react-in-jsx-scope': 'off',
      'no-unused-vars': ['error', { args: 'none', ignoreRestSiblings: true, caughtErrors: 'none' }],
      // Not caught (or not enforced) under CRA's older eslint-plugin-react-app;
      // pre-existing, deliberate, safe patterns - not worth a wide unrelated diff here.
      'no-prototype-builtins': 'off',
      'no-control-regex': 'off',
    },
  },
  {
    files: ['**/*.test.{js,jsx}', 'src/setupTests.js'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.vitest,
      },
    },
  },
  // Non-type-checked recommended rules only (no `parserOptions.project`) - fast to run,
  // revisit the type-checked variant once enough of the codebase has migrated (see
  // docs/frontend-typescript-migration-plan.md).
  ...tseslint.config({
    files: ['**/*.{ts,tsx}'],
    extends: [...tseslint.configs.recommended, react.configs.flat.recommended],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      'react/prop-types': 'off',
      'react/react-in-jsx-scope': 'off',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { args: 'none', ignoreRestSiblings: true, caughtErrors: 'none' },
      ],
    },
  }),
  {
    files: ['**/*.test.{ts,tsx}'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.vitest,
      },
    },
  },
];
