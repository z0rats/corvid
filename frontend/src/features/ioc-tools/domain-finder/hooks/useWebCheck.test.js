import { renderHook, waitFor } from '@testing-library/react';
import api from '../../../../core/services/baseApi';
import { useWebCheck } from './useWebCheck';

vi.mock('../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('useWebCheck', () => {
  it('keeps other checks intact when one check fails', async () => {
    api.get.mockImplementation((url) =>
      url.includes('/ssl-info/')
        ? Promise.reject({ message: 'connection refused' })
        : Promise.resolve({ data: { url } })
    );

    const { result } = renderHook(() => useWebCheck('example.com'));

    await waitFor(() => {
      for (const key of ['ssl', 'headers', 'dnssec', 'blocklist']) {
        expect(result.current[key].loading).toBe(false);
      }
    });
    expect(result.current.ssl.error).toBe('connection refused');
    expect(result.current.dnssec.data).toEqual({ url: '/api/domain/dnssec/example.com' });
    expect(result.current.blocklist.error).toBeNull();
  });

  it('marks a wildcard pattern as unsupported without calling the API', () => {
    const { result } = renderHook(() => useWebCheck('*.example.com'));
    expect(result.current.unsupported).toBe(true);
    expect(api.get).not.toHaveBeenCalled();
  });
});
