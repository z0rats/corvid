import { renderHook, waitFor } from '@testing-library/react';
import { useDnsLookup } from './useDnsLookup';
import { dnsLookupApi } from '../../services/api/dnsLookupApi';

vi.mock('../../services/api/dnsLookupApi');

afterEach(() => vi.clearAllMocks());

describe('useDnsLookup', () => {
  it('does nothing when no domain is given', () => {
    const { result } = renderHook(() => useDnsLookup(''));

    expect(result.current).toEqual({ data: null, loading: false, error: null, unsupported: false });
    expect(dnsLookupApi.lookupDns).not.toHaveBeenCalled();
  });

  it('fetches and stores the result for a plain domain', async () => {
    dnsLookupApi.lookupDns.mockResolvedValue({ A: ['1.2.3.4'] });
    const { result } = renderHook(() => useDnsLookup('example.com'));

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(dnsLookupApi.lookupDns).toHaveBeenCalledWith('example.com');
    expect(result.current.data).toEqual({ A: ['1.2.3.4'] });
    expect(result.current.error).toBeNull();
  });

  it('marks a wildcard search pattern as unsupported without calling the API', () => {
    const { result } = renderHook(() => useDnsLookup('*.example.com'));

    expect(result.current.unsupported).toBe(true);
    expect(dnsLookupApi.lookupDns).not.toHaveBeenCalled();
  });

  it('extracts the error detail from a failed response', async () => {
    dnsLookupApi.lookupDns.mockRejectedValue({ response: { data: { detail: 'DNS lookup failed' } } });
    const { result } = renderHook(() => useDnsLookup('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('DNS lookup failed');
    expect(result.current.data).toBeNull();
  });

  it('re-fetches when the domain prop changes', async () => {
    dnsLookupApi.lookupDns.mockResolvedValueOnce({ A: ['1.1.1.1'] }).mockResolvedValueOnce({ A: ['2.2.2.2'] });
    const { result, rerender } = renderHook(({ domain }) => useDnsLookup(domain), {
      initialProps: { domain: 'a.com' },
    });
    await waitFor(() => expect(result.current.data).toEqual({ A: ['1.1.1.1'] }));

    rerender({ domain: 'b.com' });
    await waitFor(() => expect(result.current.data).toEqual({ A: ['2.2.2.2'] }));

    expect(dnsLookupApi.lookupDns).toHaveBeenNthCalledWith(1, 'a.com');
    expect(dnsLookupApi.lookupDns).toHaveBeenNthCalledWith(2, 'b.com');
  });
});
