import { act, renderHook, waitFor } from '@testing-library/react';
import api from '../../../../core/services/baseApi';
import { useDomainPanel } from './useDomainPanel';

vi.mock('../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

const get = api.get as unknown as ReturnType<typeof vi.fn>;

afterEach(() => vi.clearAllMocks());

describe('useDomainPanel', () => {
  describe('auto mode', () => {
    it('does nothing without a domain', () => {
      const { result } = renderHook(() => useDomainPanel('ct-subdomains', ''));
      expect(get).not.toHaveBeenCalled();
      expect(result.current.data).toBeNull();
      expect(result.current.unsupported).toBe(false);
    });

    it('fetches the panel endpoint for a plain domain', async () => {
      get.mockResolvedValue({ data: { subdomains: ['www.example.com'] } });
      const { result } = renderHook(() => useDomainPanel('ct-subdomains', 'example.com'));

      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(get).toHaveBeenCalledWith('/api/domain/ct-subdomains/example.com', { params: undefined });
      expect(result.current.data).toEqual({ subdomains: ['www.example.com'] });
      expect(result.current.error).toBeNull();
    });

    it('passes params and refetches when they change', async () => {
      get.mockResolvedValue({ data: {} });
      const { rerender } = renderHook(
        ({ path }) => useDomainPanel('wayback', 'example.com', { params: path ? { path } : undefined }),
        { initialProps: { path: null as string | null } }
      );
      await waitFor(() => expect(get).toHaveBeenCalledTimes(1));

      rerender({ path: '/login' });

      await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
      expect(get).toHaveBeenLastCalledWith('/api/domain/wayback/example.com', { params: { path: '/login' } });
    });

    it('marks a wildcard pattern as unsupported without calling the API', () => {
      const { result } = renderHook(() => useDomainPanel('whois', '*.example.com'));
      expect(result.current.unsupported).toBe(true);
      expect(get).not.toHaveBeenCalled();
    });

    it.each([
      [{ response: { data: { detail: 'bad domain' } } }, 'bad domain'],
      [{ response: { data: { message: 'upstream down' } } }, 'upstream down'],
      [{ message: 'network down' }, 'network down']
    ])('extracts the error message from %j', async (err, expected) => {
      get.mockRejectedValue(err);
      const { result } = renderHook(() => useDomainPanel('dns', 'example.com'));

      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(result.current.error).toBe(expected);
      expect(result.current.data).toBeNull();
    });

    it('reports a missing API key as notConfigured, not as an error', async () => {
      get.mockRejectedValue({ response: { data: { error_code: 'DNSDUMPSTER_NOT_CONFIGURED' } } });
      const { result } = renderHook(() =>
        useDomainPanel('dnsdumpster', 'example.com', { notConfiguredCode: 'DNSDUMPSTER_NOT_CONFIGURED' })
      );

      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(result.current.notConfigured).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it('ignores a response for a domain that is no longer current', async () => {
      let resolveFirst: (value: unknown) => void = () => {};
      get
        .mockImplementationOnce(() => new Promise((resolve) => { resolveFirst = resolve; }))
        .mockResolvedValueOnce({ data: { domain: 'second' } });
      const { result, rerender } = renderHook(({ domain }) => useDomainPanel('whois', domain), {
        initialProps: { domain: 'first.com' }
      });

      rerender({ domain: 'second.com' });
      await waitFor(() => expect(result.current.data).toEqual({ domain: 'second' }));
      await act(async () => resolveFirst({ data: { domain: 'first' } }));

      expect(result.current.data).toEqual({ domain: 'second' });
    });
  });

  describe('manual mode', () => {
    it('waits for run()', async () => {
      get.mockResolvedValue({ data: { reachable: true } });
      const { result } = renderHook(() => useDomainPanel('host-probe', 'example.com', { auto: false }));
      expect(get).not.toHaveBeenCalled();

      await act(() => result.current.run());

      expect(get).toHaveBeenCalledWith('/api/domain/host-probe/example.com', { params: undefined });
      expect(result.current.data).toEqual({ reachable: true });
    });
  });
});
