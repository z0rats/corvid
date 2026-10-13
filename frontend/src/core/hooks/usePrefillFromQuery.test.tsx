import { renderHook } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router';
import type { ReactNode } from 'react';
import { usePrefillFromQuery } from './usePrefillFromQuery';
import { buildPrefillUrl } from '../utils/crossFeatureNav';

function wrapperFor(url: string) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <MemoryRouter initialEntries={[url]}>{children}</MemoryRouter>;
  };
}

describe('usePrefillFromQuery context params', () => {
  it('hands the pivot context (parent/site/src) to onValue and strips it with q', () => {
    const onValue = vi.fn();
    const { result } = renderHook(
      () => ({ value: usePrefillFromQuery(onValue), search: useLocation().search }),
      { wrapper: wrapperFor('/x?q=bob&parent=7&site=GitHub&src=link&other=keep') },
    );

    expect(onValue).toHaveBeenCalledTimes(1);
    expect(onValue).toHaveBeenCalledWith('bob', { parent: '7', site: 'GitHub', src: 'link' });
    expect(result.current.search).toBe('?other=keep');
  });

  it('reports absent context params as null', () => {
    const onValue = vi.fn();
    renderHook(() => usePrefillFromQuery(onValue), { wrapper: wrapperFor('/x?q=bob') });

    expect(onValue).toHaveBeenCalledWith('bob', { parent: null, site: null, src: null });
  });
});

describe('buildPrefillUrl', () => {
  it('encodes the value and appends only the context that is set', () => {
    expect(buildPrefillUrl('/p', 'a b')).toBe('/p?q=a+b');
    expect(buildPrefillUrl('/p', 'bob', { parent: 7, site: undefined, src: 'x&y' })).toBe('/p?q=bob&parent=7&src=x%26y');
  });
});
