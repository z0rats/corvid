import { renderHook, waitFor } from '@testing-library/react';
import { useRapidDnsSubdomains } from './useRapidDnsSubdomains';
import { rapidDnsApi } from '../../services/api/rapidDnsApi';

vi.mock('../../services/api/rapidDnsApi');

afterEach(() => vi.clearAllMocks());

describe('useRapidDnsSubdomains', () => {
  it('does nothing when no domain is given', () => {
    const { result } = renderHook(() => useRapidDnsSubdomains(''));
    expect(rapidDnsApi.lookupRapidDnsSubdomains).not.toHaveBeenCalled();
    expect(result.current.data).toBeNull();
  });

  it('fetches subdomains for a plain domain', async () => {
    rapidDnsApi.lookupRapidDnsSubdomains.mockResolvedValue({
      subdomains: ['www.example.com'],
      total_records: 1
    });
    const { result } = renderHook(() => useRapidDnsSubdomains('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual({ subdomains: ['www.example.com'], total_records: 1 });
  });

  it('marks a wildcard pattern as unsupported without calling the API', () => {
    const { result } = renderHook(() => useRapidDnsSubdomains('*.example.com'));
    expect(result.current.unsupported).toBe(true);
    expect(rapidDnsApi.lookupRapidDnsSubdomains).not.toHaveBeenCalled();
  });

  it('extracts an error message on failure', async () => {
    rapidDnsApi.lookupRapidDnsSubdomains.mockRejectedValue({ message: 'network down' });
    const { result } = renderHook(() => useRapidDnsSubdomains('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('network down');
  });

  it('refetches when the domain changes', async () => {
    rapidDnsApi.lookupRapidDnsSubdomains.mockResolvedValue({ subdomains: [] });
    const { result, rerender } = renderHook(
      ({ domain }) => useRapidDnsSubdomains(domain),
      { initialProps: { domain: 'example.com' } }
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(rapidDnsApi.lookupRapidDnsSubdomains).toHaveBeenCalledWith('example.com');

    rerender({ domain: 'other.com' });
    await waitFor(() =>
      expect(rapidDnsApi.lookupRapidDnsSubdomains).toHaveBeenCalledWith('other.com')
    );
  });
});
