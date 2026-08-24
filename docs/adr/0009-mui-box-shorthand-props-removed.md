# Style Box/Stack/Grid only through `sx`, never top-level shorthand props

`@mui/material`/`@mui/system` 9.x's `styleFunctionSx` (the style interpolation function behind
`createBox`, and reused by `Stack`/`Grid`) only reads the `sx` prop:

```js
function styleFunctionSx(props) {
  if (!props.sx) return null;
  ...
}
```

Earlier MUI versions additionally read a long list of top-level shorthand props directly off
`props` (`display`, `p`/`m`/`px`/... spacing, `justifyContent`, `flexWrap`, `bgcolor`, etc.) and
turned them into CSS the same way `sx` keys do. That composed "system props" behavior is gone in
this version — a prop like `<Box display="flex">` is no longer recognized by the style function at
all. `Box`'s `shouldForwardProp` still forwards it, though, straight onto the underlying `div` as
an invalid DOM attribute: the prop is silently a no-op for styling and only shows up as a
"React does not recognize the `X` prop on a DOM element" console warning — nothing fails loudly.

This was discovered after ~65 files had accumulated this pattern from before the dependency bump,
several with genuinely broken layouts as a result (an `ai-templates` split view that should render
side-by-side collapsed to a full-width vertical stack because `display="flex"` was inert). All
existing usages were migrated to `sx={{ ... }}` in one pass; `eslint.config.mjs`'s
`no-restricted-syntax` rule now flags any shorthand style prop (the same list this migration used)
passed directly to `Box`, `Stack`, or `Grid`, so the pattern can't quietly return.

`Stack`'s own dedicated props (`direction`, `spacing`, `divider`, `useFlexGap`) and `Grid`'s
(`container`, `size`, `columns`, `columnSpacing`, `rowSpacing`, `direction`, `wrap`, `offset`) are
unaffected — those are handled by each component's own destructuring, not `styleFunctionSx`, and
are excluded from the lint rule.
