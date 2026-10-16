/**
 * The longest tab path the current location sits under, so a detail route
 * (`/username-search/history/42`) still marks its parent tab, and a nested path that is itself a
 * tab (`/ioc-tools/lookup/history`) wins over its shorter sibling (`/ioc-tools/lookup`).
 */
export function findActiveTabPath(tabs, pathname) {
  return tabs
    .map((tab) => tab.path)
    .filter((path) => pathname === path || pathname.startsWith(`${path}/`))
    .sort((a, b) => b.length - a.length)[0] ?? false;
}
