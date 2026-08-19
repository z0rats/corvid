import { act, renderHook, waitFor } from '@testing-library/react';
import { useDomainSearch } from './useDomainSearch';
import { domainMonitoringApi } from '../../services/api/domainMonitoringApi';

vi.mock('../../services/api/domainMonitoringApi');

afterEach(() => vi.clearAllMocks());

describe('useDomainSearch', () => {
  it('does nothing when no domain is given', () => {
    const { result } = renderHook(() => useDomainSearch(''));
    expect(domainMonitoringApi.searchDomains).not.toHaveBeenCalled();
    expect(result.current.data).toBeNull();
  });

  it('searches and stores the result on mount', async () => {
    domainMonitoringApi.searchDomains.mockResolvedValue({ matches: ['example.com'] });
    const { result } = renderHook(() => useDomainSearch('exa*'));

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(domainMonitoringApi.searchDomains).toHaveBeenCalledWith('exa*');
    expect(result.current.data).toEqual({ matches: ['example.com'] });
  });

  it('surfaces a plain error message on failure (no response-shape spelunking)', async () => {
    domainMonitoringApi.searchDomains.mockRejectedValue(new Error('search failed'));
    const { result } = renderHook(() => useDomainSearch('exa*'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('search failed');
  });

  it('falls back to a generic message when the error has none', async () => {
    domainMonitoringApi.searchDomains.mockRejectedValue(new Error());
    const { result } = renderHook(() => useDomainSearch('exa*'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Failed to search domains');
  });

  it('refetch re-runs the search for the current domain', async () => {
    domainMonitoringApi.searchDomains
      .mockResolvedValueOnce({ matches: ['first'] })
      .mockResolvedValueOnce({ matches: ['second'] });
    const { result } = renderHook(() => useDomainSearch('exa*'));
    await waitFor(() => expect(result.current.data).toEqual({ matches: ['first'] }));

    await act(async () => {
      result.current.refetch();
    });

    expect(result.current.data).toEqual({ matches: ['second'] });
    expect(domainMonitoringApi.searchDomains).toHaveBeenCalledTimes(2);
  });

  it('refetch is a no-op when there is no domain', () => {
    const { result } = renderHook(() => useDomainSearch(''));

    result.current.refetch();

    expect(domainMonitoringApi.searchDomains).not.toHaveBeenCalled();
  });
});
