import { renderHook, waitFor } from '@testing-library/react';
import { useWebCheck } from './useWebCheck';
import { webCheckApi } from '../../services/api/webCheckApi';

vi.mock('../../services/api/webCheckApi');

afterEach(() => vi.clearAllMocks());

describe('useWebCheck', () => {
  it('does nothing when no domain is given', () => {
    const { result } = renderHook(() => useWebCheck(''));
    expect(webCheckApi.getSslInfo).not.toHaveBeenCalled();
    expect(result.current.ssl.data).toBeNull();
  });

  it('marks a wildcard pattern as unsupported without calling the API', () => {
    const { result } = renderHook(() => useWebCheck('*.example.com'));
    expect(result.current.unsupported).toBe(true);
    expect(webCheckApi.getSslInfo).not.toHaveBeenCalled();
  });

  it('fetches all four checks independently for a plain domain', async () => {
    webCheckApi.getSslInfo.mockResolvedValue({ issuer: 'CN=Test CA' });
    webCheckApi.getSecurityHeaders.mockResolvedValue({ present_headers: {} });
    webCheckApi.getDnssec.mockResolvedValue({ dnssec_enabled: true });
    webCheckApi.getBlocklist.mockResolvedValue({ flagged_count: 0 });

    const { result } = renderHook(() => useWebCheck('example.com'));

    await waitFor(() => expect(result.current.ssl.loading).toBe(false));
    await waitFor(() => expect(result.current.headers.loading).toBe(false));
    await waitFor(() => expect(result.current.dnssec.loading).toBe(false));
    await waitFor(() => expect(result.current.blocklist.loading).toBe(false));

    expect(result.current.ssl.data).toEqual({ issuer: 'CN=Test CA' });
    expect(result.current.dnssec.data).toEqual({ dnssec_enabled: true });
  });

  it('keeps other checks intact when one check fails', async () => {
    webCheckApi.getSslInfo.mockRejectedValue({ message: 'connection refused' });
    webCheckApi.getSecurityHeaders.mockResolvedValue({ present_headers: {} });
    webCheckApi.getDnssec.mockResolvedValue({ dnssec_enabled: false });
    webCheckApi.getBlocklist.mockResolvedValue({ flagged_count: 0 });

    const { result } = renderHook(() => useWebCheck('example.com'));

    await waitFor(() => expect(result.current.ssl.loading).toBe(false));
    await waitFor(() => expect(result.current.headers.loading).toBe(false));

    expect(result.current.ssl.error).toBe('connection refused');
    expect(result.current.ssl.data).toBeNull();
    expect(result.current.headers.data).toEqual({ present_headers: {} });
  });

  it('refetches all checks when the domain changes', async () => {
    webCheckApi.getSslInfo.mockResolvedValue({});
    webCheckApi.getSecurityHeaders.mockResolvedValue({});
    webCheckApi.getDnssec.mockResolvedValue({});
    webCheckApi.getBlocklist.mockResolvedValue({});

    const { result, rerender } = renderHook(({ domain }) => useWebCheck(domain), {
      initialProps: { domain: 'example.com' }
    });

    await waitFor(() => expect(result.current.ssl.loading).toBe(false));
    expect(webCheckApi.getSslInfo).toHaveBeenCalledWith('example.com');

    rerender({ domain: 'other.com' });
    await waitFor(() => expect(webCheckApi.getSslInfo).toHaveBeenCalledWith('other.com'));
  });
});
