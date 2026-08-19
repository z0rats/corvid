import { act, renderHook, waitFor } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useServiceDefinitions } from './useServiceDefinitions';
import { apiKeysState } from '../../../../../core/state/atoms';
import { iocLookupApi } from '../../../shared/services/api/iocLookupApi';

vi.mock('../../../shared/services/api/iocLookupApi');

// apiKeysState is module-scoped, so it doesn't reset between tests on its own.
function resetApiKeys() {
  const { result } = renderHook(() => useSetAtom(apiKeysState));
  act(() => result.current({}));
}

beforeEach(resetApiKeys);
afterEach(() => vi.clearAllMocks());

describe('useServiceDefinitions', () => {
  it('fetches definitions on mount', async () => {
    iocLookupApi.fetchServiceDefinitions.mockResolvedValue({
      abuseipdb: { isAvailable: true },
    });
    const { result } = renderHook(() => useServiceDefinitions());

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.serviceDefinitions).toEqual({ abuseipdb: { isAvailable: true } });
    expect(result.current.error).toBeNull();
  });

  it('sets an error message on failure', async () => {
    iocLookupApi.fetchServiceDefinitions.mockRejectedValue(new Error('network down'));
    const { result } = renderHook(() => useServiceDefinitions());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Failed to load service definitions');
  });

  it('availableServices includes only services marked isAvailable', async () => {
    iocLookupApi.fetchServiceDefinitions.mockResolvedValue({
      abuseipdb: { isAvailable: true },
      virustotal: { isAvailable: false },
    });
    const { result } = renderHook(() => useServiceDefinitions());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(Object.keys(result.current.availableServices)).toEqual(['abuseipdb']);
  });

  it('isServiceAvailable reflects a service\'s isAvailable flag, defaulting to false', async () => {
    iocLookupApi.fetchServiceDefinitions.mockResolvedValue({ abuseipdb: { isAvailable: true } });
    const { result } = renderHook(() => useServiceDefinitions());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.isServiceAvailable('abuseipdb')).toBe(true);
    expect(result.current.isServiceAvailable('not_a_real_service')).toBe(false);
  });

  it('refetch triggers another fetch', async () => {
    iocLookupApi.fetchServiceDefinitions.mockResolvedValue({});
    const { result } = renderHook(() => useServiceDefinitions());
    await waitFor(() => expect(result.current.loading).toBe(false));
    iocLookupApi.fetchServiceDefinitions.mockClear();

    act(() => result.current.refetch());

    await waitFor(() => expect(iocLookupApi.fetchServiceDefinitions).toHaveBeenCalledTimes(1));
  });

  it('re-fetches when api key availability changes', async () => {
    iocLookupApi.fetchServiceDefinitions.mockResolvedValue({});
    const { result: setApiKeys } = renderHook(() => useSetAtom(apiKeysState));
    renderHook(() => useServiceDefinitions());
    await waitFor(() => expect(iocLookupApi.fetchServiceDefinitions).toHaveBeenCalledTimes(1));

    act(() => setApiKeys.current({ abuseipdb: 'a-key' }));

    await waitFor(() => expect(iocLookupApi.fetchServiceDefinitions).toHaveBeenCalledTimes(2));
  });
});
