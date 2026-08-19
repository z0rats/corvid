import { act, renderHook } from '@testing-library/react';
import { useTemplateSearch } from './useTemplateSearch';

const templates = [
  { title: 'Log Analysis', description: 'Analyze log data for anomalies' },
  { title: 'Phishing Check', description: 'Scan email text for phishing' },
  { title: 'Code Explain', description: null },
];

describe('useTemplateSearch', () => {
  it('returns every template unfiltered when the search is empty', () => {
    const { result } = renderHook(() => useTemplateSearch(templates));

    expect(result.current.filtered).toBe(templates);
    expect(result.current.isSearching).toBe(false);
  });

  it('filters by a case-insensitive title match', () => {
    const { result } = renderHook(() => useTemplateSearch(templates));

    act(() => result.current.setSearch('phishing'));

    expect(result.current.filtered).toEqual([templates[1]]);
    expect(result.current.isSearching).toBe(true);
  });

  it('filters by a match in the description', () => {
    const { result } = renderHook(() => useTemplateSearch(templates));

    act(() => result.current.setSearch('anomalies'));

    expect(result.current.filtered).toEqual([templates[0]]);
  });

  it('does not throw on a template with a null description', () => {
    const { result } = renderHook(() => useTemplateSearch(templates));

    act(() => result.current.setSearch('explain'));

    expect(result.current.filtered).toEqual([templates[2]]);
  });

  it('treats a whitespace-only search as no search', () => {
    const { result } = renderHook(() => useTemplateSearch(templates));

    act(() => result.current.setSearch('   '));

    expect(result.current.filtered).toBe(templates);
    expect(result.current.isSearching).toBe(false);
  });
});
