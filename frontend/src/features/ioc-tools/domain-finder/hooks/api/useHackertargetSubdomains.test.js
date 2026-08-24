import { renderHook, waitFor } from '@testing-library/react';
import { useHackertargetSubdomains } from './useHackertargetSubdomains';
import { hackertargetApi } from '../../services/api/hackertargetApi';

vi.mock('../../services/api/hackertargetApi');

afterEach(() => vi.clearAllMocks());

describe('useHackertargetSubdomains', () => {
  it('does nothing when no domain is given', () => {
    const { result } = renderHook(() => useHackertargetSubdomains(''));
    expect(hackertargetApi.lookupHackertargetSubdomains).not.toHaveBeenCalled();
    expect(result.current.data).toBeNull();
  });

  it('fetches subdomains for a plain domain', async () => {
    hackertargetApi.lookupHackertargetSubdomains.mockResolvedValue({
      subdomains: ['www.example.com'],
      total_hosts: 1
    });
    const { result } = renderHook(() => useHackertargetSubdomains('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual({ subdomains: ['www.example.com'], total_hosts: 1 });
  });

  it('marks a wildcard pattern as unsupported without calling the API', () => {
    const { result } = renderHook(() => useHackertargetSubdomains('*.example.com'));
    expect(result.current.unsupported).toBe(true);
    expect(hackertargetApi.lookupHackertargetSubdomains).not.toHaveBeenCalled();
  });

  it('extracts an error message on failure', async () => {
    hackertargetApi.lookupHackertargetSubdomains.mockRejectedValue({ message: 'network down' });
    const { result } = renderHook(() => useHackertargetSubdomains('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('network down');
  });

  it('refetches when the domain changes', async () => {
    hackertargetApi.lookupHackertargetSubdomains.mockResolvedValue({ subdomains: [] });
    const { result, rerender } = renderHook(
      ({ domain }) => useHackertargetSubdomains(domain),
      { initialProps: { domain: 'example.com' } }
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(hackertargetApi.lookupHackertargetSubdomains).toHaveBeenCalledWith('example.com');

    rerender({ domain: 'other.com' });
    await waitFor(() =>
      expect(hackertargetApi.lookupHackertargetSubdomains).toHaveBeenCalledWith('other.com')
    );
  });
});
