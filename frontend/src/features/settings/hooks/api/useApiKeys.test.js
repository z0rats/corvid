import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useApiKeys } from './useApiKeys';
import { settingsApi } from '../../services/api/settingsApi';
import { apiKeysState } from '../../../../core/state/atoms';

vi.mock('../../services/api/settingsApi');

function resetApiKeys() {
  const { result } = renderHook(() => useSetAtom(apiKeysState));
  act(() => result.current({}));
}

beforeEach(resetApiKeys);
afterEach(() => vi.clearAllMocks());

describe('useApiKeys — refreshApiKeys', () => {
  it('fetches and stores active keys', async () => {
    settingsApi.getActiveApiKeys.mockResolvedValue({ abuseipdb: true });
    const { result } = renderHook(() => useApiKeys());

    let returned;
    await act(async () => { returned = await result.current.refreshApiKeys(); });

    expect(returned).toEqual({ abuseipdb: true });
  });

  it('rethrows on failure', async () => {
    settingsApi.getActiveApiKeys.mockRejectedValue(new Error('down'));
    const { result } = renderHook(() => useApiKeys());

    await expect(result.current.refreshApiKeys()).rejects.toThrow('down');
  });
});

describe('useApiKeys — getServicesConfig', () => {
  it('wraps the config in a success result', async () => {
    settingsApi.getServicesConfig.mockResolvedValue({ abuseipdb: {} });
    const { result } = renderHook(() => useApiKeys());

    let returned;
    await act(async () => { returned = await result.current.getServicesConfig(); });

    expect(returned).toMatchObject({ success: true, data: { abuseipdb: {} } });
  });
});

describe('useApiKeys — getKeyStatus', () => {
  it('reports the primary key as configured and the service as active', async () => {
    settingsApi.getConfiguredApiKeys.mockResolvedValue({ abuseipdb: true });
    settingsApi.getActiveApiKeys.mockResolvedValue({ abuseipdb: true });
    const { result } = renderHook(() => useApiKeys());

    let returned;
    await act(async () => { returned = await result.current.getKeyStatus('abuseipdb'); });

    expect(returned.data).toEqual({ existsInBackend: true, isServiceActive: true });
  });

  it('treats the service as active if any related key is active', async () => {
    settingsApi.getConfiguredApiKeys.mockResolvedValue({ google_client_id: true });
    settingsApi.getActiveApiKeys.mockResolvedValue({ google_client_secret: true });
    const { result } = renderHook(() => useApiKeys());

    let returned;
    await act(async () => {
      returned = await result.current.getKeyStatus('google_client_id', ['google_client_secret']);
    });

    expect(returned.data).toEqual({ existsInBackend: true, isServiceActive: true });
  });
});

describe('useApiKeys — saveApiKey', () => {
  it('creates the key and refreshes on success', async () => {
    settingsApi.createApiKey.mockResolvedValue({});
    settingsApi.getActiveApiKeys.mockResolvedValue({});
    const { result } = renderHook(() => useApiKeys());

    let returned;
    await act(async () => { returned = await result.current.saveApiKey('abuseipdb', 'secret'); });

    expect(settingsApi.createApiKey).toHaveBeenCalledWith('abuseipdb', 'secret');
    expect(settingsApi.getActiveApiKeys).toHaveBeenCalled();
    expect(returned).toMatchObject({ success: true });
  });

  it('falls back to update when the key already exists (409)', async () => {
    settingsApi.createApiKey.mockRejectedValue({ response: { status: 409 } });
    settingsApi.updateApiKey.mockResolvedValue({});
    settingsApi.getActiveApiKeys.mockResolvedValue({});
    const { result } = renderHook(() => useApiKeys());

    await act(async () => { await result.current.saveApiKey('abuseipdb', 'secret'); });

    expect(settingsApi.updateApiKey).toHaveBeenCalledWith('abuseipdb', 'secret');
  });

  it('surfaces a non-409 failure without falling back to update', async () => {
    settingsApi.createApiKey.mockRejectedValue({ response: { status: 500 } });
    const { result } = renderHook(() => useApiKeys());

    let returned;
    await act(async () => { returned = await result.current.saveApiKey('abuseipdb', 'secret'); });

    expect(settingsApi.updateApiKey).not.toHaveBeenCalled();
    expect(returned.success).toBe(false);
  });
});

describe('useApiKeys — deleteApiKey', () => {
  it('clears the key and refreshes', async () => {
    settingsApi.updateApiKey.mockResolvedValue({});
    settingsApi.getActiveApiKeys.mockResolvedValue({});
    const { result } = renderHook(() => useApiKeys());

    await act(async () => { await result.current.deleteApiKey('abuseipdb'); });

    expect(settingsApi.updateApiKey).toHaveBeenCalledWith('abuseipdb', '', false, false);
  });
});

describe('useApiKeys — toggleServiceActivation', () => {
  it('activates all related keys when currently inactive', async () => {
    settingsApi.updateApiKeyStatus.mockResolvedValue({});
    settingsApi.getActiveApiKeys.mockResolvedValue({});
    const { result } = renderHook(() => useApiKeys());

    let returned;
    await act(async () => {
      returned = await result.current.toggleServiceActivation(
        ['abuseipdb'], false, 'AbuseIPDB',
      );
    });

    expect(settingsApi.updateApiKeyStatus).toHaveBeenCalledWith('abuseipdb', true);
    expect(returned).toMatchObject({ success: true, isActive: true });
  });

  it('deactivates all related keys when currently active', async () => {
    settingsApi.updateApiKeyStatus.mockResolvedValue({});
    settingsApi.getActiveApiKeys.mockResolvedValue({});
    const { result } = renderHook(() => useApiKeys());

    let returned;
    await act(async () => {
      returned = await result.current.toggleServiceActivation(
        ['abuseipdb'], true, 'AbuseIPDB',
      );
    });

    expect(settingsApi.updateApiKeyStatus).toHaveBeenCalledWith('abuseipdb', false);
    expect(returned.isActive).toBe(false);
  });
});
