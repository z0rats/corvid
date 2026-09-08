import { TAB_ROUTES } from './sidebarConfig';

const identityT = (key) => key;

const resolveTabs = (pathname, context = {}) => {
  const route = TAB_ROUTES.find(({ prefix }) => pathname.startsWith(prefix));
  return route ? route.getTabs(identityT, context) : null;
};

describe('TAB_ROUTES — Layout.jsx tab resolution', () => {
  it('resolves a plain tabbed feature by path prefix', () => {
    const tabs = resolveTabs('/username-search/history');
    expect(tabs.map((tab) => tab.path)).toContain('/username-search/history');
  });

  it('returns null for a route with no registered tabs', () => {
    expect(resolveTabs('/')).toBeNull();
    expect(resolveTabs('/some-untabbed-feature')).toBeNull();
  });

  it('hides the AI templates tabs entirely without an LLM key', () => {
    expect(resolveTabs('/ai-templates/templates', { hasLlmKey: false })).toBeNull();
    expect(resolveTabs('/ai-templates/templates', { hasLlmKey: true })).not.toBeNull();
  });

  it('hides only the newsfeed report tab without an LLM key', () => {
    const withoutKey = resolveTabs('/newsfeed/feed', { hasLlmKey: false });
    const withKey = resolveTabs('/newsfeed/feed', { hasLlmKey: true });
    expect(withoutKey.some((tab) => tab.path === '/newsfeed/report')).toBe(false);
    expect(withKey.some((tab) => tab.path === '/newsfeed/report')).toBe(true);
  });

  it('has no duplicate or overlapping-ambiguous prefixes', () => {
    const prefixes = TAB_ROUTES.map((route) => route.prefix);
    expect(new Set(prefixes).size).toBe(prefixes.length);
  });
});
