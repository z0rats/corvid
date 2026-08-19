import { act, renderHook } from '@testing-library/react';
import { useQuota } from './useQuota';
import { settingsApi } from '../../services/api/settingsApi';

vi.mock('../../services/api/settingsApi');

afterEach(() => vi.clearAllMocks());

describe('useQuota — refreshQuota', () => {
  it('starts with an empty list and no loading', () => {
    const { result } = renderHook(() => useQuota());

    expect(result.current).toMatchObject({ quotas: [], loading: false, error: null });
  });

  it('fetches and stores quota data', async () => {
    settingsApi.getQuotaStatus.mockResolvedValue([{ service: 'abuseipdb', used: 10 }]);
    const { result } = renderHook(() => useQuota());

    let returned;
    await act(async () => { returned = await result.current.refreshQuota(); });

    expect(result.current.quotas).toEqual([{ service: 'abuseipdb', used: 10 }]);
    expect(result.current.loading).toBe(false);
    expect(returned).toMatchObject({ success: true, data: [{ service: 'abuseipdb', used: 10 }] });
  });

  it('prefers the response detail message on failure', async () => {
    settingsApi.getQuotaStatus.mockRejectedValue({ response: { data: { detail: 'Quota unavailable' } } });
    const { result } = renderHook(() => useQuota());

    let returned;
    await act(async () => { returned = await result.current.refreshQuota(); });

    expect(result.current.error).toBe('Quota unavailable');
    expect(result.current.loading).toBe(false);
    expect(returned).toEqual({ success: false, message: 'Quota unavailable' });
  });

  it('falls back to the quota load-error message', async () => {
    settingsApi.getQuotaStatus.mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useQuota());

    await act(async () => { await result.current.refreshQuota(); });

    expect(result.current.error).toBe('Failed to load quota status.');
  });
});
