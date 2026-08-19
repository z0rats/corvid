import { act, renderHook } from '@testing-library/react';
import { useApiKeyFilters } from './useFilters';

const config = {
  abuseipdb: { name: 'AbuseIPDB', available: true },
  virustotal: { name: 'VirusTotal', available: false },
};

describe('useApiKeyFilters', () => {
  it('starts with no search and shows all services', () => {
    const { result } = renderHook(() => useApiKeyFilters(config));

    expect(result.current.searchFilter).toBe('');
    expect(result.current.showOnlyConfigured).toBe(false);
    expect(result.current.filteredServices.map(([key]) => key).sort()).toEqual([
      'abuseipdb',
      'virustotal',
    ]);
  });

  it('updateSearchFilter narrows filteredServices', () => {
    const { result } = renderHook(() => useApiKeyFilters(config));

    act(() => result.current.updateSearchFilter('virus'));

    expect(result.current.filteredServices.map(([key]) => key)).toEqual(['virustotal']);
  });

  it('toggleShowOnlyConfigured flips the flag and narrows to available services', () => {
    const { result } = renderHook(() => useApiKeyFilters(config));

    act(() => result.current.toggleShowOnlyConfigured());

    expect(result.current.showOnlyConfigured).toBe(true);
    expect(result.current.filteredServices.map(([key]) => key)).toEqual(['abuseipdb']);
  });

  it('clearFilters resets both search and the configured-only flag', () => {
    const { result } = renderHook(() => useApiKeyFilters(config));
    act(() => result.current.updateSearchFilter('virus'));
    act(() => result.current.toggleShowOnlyConfigured());

    act(() => result.current.clearFilters());

    expect(result.current.searchFilter).toBe('');
    expect(result.current.showOnlyConfigured).toBe(false);
  });
});
