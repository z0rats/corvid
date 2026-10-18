import js from '@eslint/js';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import globals from 'globals';
import tseslint from 'typescript-eslint';

// MUI 9's Box/Stack/Grid only read the `sx` prop for styling - the legacy top-level
// shorthand style props (display, p, m, justifyContent, ...) that older MUI versions
// supported are silently forwarded as invalid DOM attributes and do nothing. Move them
// into `sx` instead. See docs/adr/0009-mui-box-shorthand-props-removed.md.
const MUI_STYLE_SHORTHAND_PROPS = [
  'display', 'position', 'top', 'right', 'bottom', 'left', 'zIndex',
  'overflow', 'overflowX', 'overflowY',
  'flexDirection', 'flexWrap', 'flexGrow', 'flexShrink', 'flexBasis', 'flex',
  'justifyContent', 'alignItems', 'alignContent', 'alignSelf', 'order',
  'gap', 'rowGap', 'columnGap',
  'width', 'maxWidth', 'minWidth', 'height', 'maxHeight', 'minHeight', 'boxSizing',
  'm', 'mt', 'mr', 'mb', 'ml', 'mx', 'my', 'margin', 'marginTop', 'marginRight', 'marginBottom', 'marginLeft',
  'p', 'pt', 'pr', 'pb', 'pl', 'px', 'py', 'padding', 'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft',
  'bgcolor', 'color', 'border', 'borderTop', 'borderRight', 'borderBottom', 'borderLeft',
  'borderColor', 'borderRadius', 'boxShadow',
  'textAlign', 'visibility', 'whiteSpace', 'textOverflow',
  'fontSize', 'fontWeight', 'fontFamily', 'fontStyle', 'letterSpacing', 'lineHeight',
];
const muiBoxShorthandPropSelector =
  `JSXOpeningElement[name.name=/^(Box|Stack|Grid)$/] > ` +
  `JSXAttribute[name.name=/^(${MUI_STYLE_SHORTHAND_PROPS.join('|')})$/]`;

// No eslint-plugin-react (~95 transitive packages for a handful of rules): ESLint 10's scope
// analysis already tracks JSX references, so no-unused-vars/no-undef cover jsx-uses-vars/
// jsx-no-undef. This selector stands in for react/jsx-key on the common `.map(x => <El/>)` shape.
const MAP_CALLBACK = `CallExpression[callee.property.name=/^(map|flatMap)$/] > :function`;
const missingKeySelector = [
  `${MAP_CALLBACK} > JSXElement > JSXOpeningElement:not(:has(JSXAttribute[name.name="key"]))`,
  `${MAP_CALLBACK} > BlockStatement > ReturnStatement > JSXElement > JSXOpeningElement:not(:has(JSXAttribute[name.name="key"]))`,
  `${MAP_CALLBACK} > JSXFragment`,
  `${MAP_CALLBACK} > BlockStatement > ReturnStatement > JSXFragment`,
].join(', ');

const restrictedSyntax = [
  'error',
  {
    selector: muiBoxShorthandPropSelector,
    message:
      'MUI 9 Box/Stack/Grid no longer apply this as a top-level prop - move it into sx={{ ... }}.',
  },
  {
    selector: missingKeySelector,
    message: 'Elements returned from .map() need a `key` prop (use <Fragment key=...> instead of <>).',
  },
];

export default [
  { ignores: ['build/**', 'node_modules/**', 'coverage/**'] },
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      parserOptions: { ecmaFeatures: { jsx: true } },
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
      // Automatic JSX runtime: a leftover `import React` is harmless, not worth a ~300-file diff.
      'no-unused-vars': ['error', { args: 'none', ignoreRestSiblings: true, caughtErrors: 'none', varsIgnorePattern: '^React$' }],
      // Not caught (or not enforced) under CRA's older eslint-plugin-react-app;
      // pre-existing, deliberate, safe patterns - not worth a wide unrelated diff here.
      'no-prototype-builtins': 'off',
      'no-control-regex': 'off',
      'no-restricted-syntax': restrictedSyntax,
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
  // revisit the type-checked variant once enough of the codebase has migrated.
  ...tseslint.config({
    files: ['**/*.{ts,tsx}'],
    extends: [...tseslint.configs.recommended],
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
      '@typescript-eslint/no-unused-vars': [
        'error',
        { args: 'none', ignoreRestSiblings: true, caughtErrors: 'none' },
      ],
      'no-restricted-syntax': restrictedSyntax,
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
