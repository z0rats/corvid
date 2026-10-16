import { findActiveTabPath } from './activeTab';

const tabs = [
  { path: '/ioc-tools/lookup' },
  { path: '/ioc-tools/lookup/history' },
  { path: '/ioc-tools/bulk' },
];

describe('findActiveTabPath', () => {
  it('matches a tab path exactly', () => {
    expect(findActiveTabPath(tabs, '/ioc-tools/bulk')).toBe('/ioc-tools/bulk');
  });

  it('prefers the longest matching tab over its shorter sibling', () => {
    expect(findActiveTabPath(tabs, '/ioc-tools/lookup/history')).toBe('/ioc-tools/lookup/history');
    expect(findActiveTabPath(tabs, '/ioc-tools/lookup/history/7')).toBe('/ioc-tools/lookup/history');
  });

  it('keeps a detail route under its parent tab', () => {
    expect(findActiveTabPath(tabs, '/ioc-tools/bulk/42')).toBe('/ioc-tools/bulk');
  });

  it('does not treat a shared string prefix as a parent segment', () => {
    expect(findActiveTabPath([{ path: '/amass/new' }], '/amass/newer')).toBe(false);
  });

  it('returns false when nothing matches', () => {
    expect(findActiveTabPath(tabs, '/ioc-tools')).toBe(false);
  });
});
