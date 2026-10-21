import { renderHook, act, waitFor } from '@testing-library/react';
import { Provider, createStore } from 'jotai';
import { createElement } from 'react';
import { useHealthCheck } from './useHealthCheck';
import { healthService } from '../../services/api/healthService';
import { appVersionAtom } from '../../state/atoms';
import { alertsService } from '../../services/api/alertsService';
import { settingsService } from '../../services/api/settingsService';
import api from '../../services/baseApi';

vi.mock('../../services/api/healthService', () => ({ healthService: { checkBackendHealth: vi.fn() } }));
vi.mock('../../services/baseApi', () => ({
  default: { get: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

function setup() {
  const store = createStore();
  const wrapper = ({ children }) => createElement(Provider, { store }, children);
  const hook = renderHook(() => useHealthCheck(), { wrapper });
  return { ...hook, store };
}

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe('useHealthCheck', () => {
  it('goes healthy and publishes the backend version', async () => {
    healthService.checkBackendHealth.mockResolvedValue({ status: 'ok', version: '1.4.0' });
    const { result, store } = setup();
    expect(result.current.status).toBe('loading');
    await waitFor(() => expect(result.current.status).toBe('healthy'));
    expect(store.get(appVersionAtom)).toBe('1.4.0');
  });

  it.each([
    ['unhealthy payload', () => healthService.checkBackendHealth.mockResolvedValue({ status: 'unhealthy' })],
    ['network error', () => healthService.checkBackendHealth.mockRejectedValue(new Error('ECONNREFUSED'))],
  ])('%s -> error, and retry recovers', async (_label, arrange) => {
    arrange();
    const { result } = setup();
    await waitFor(() => expect(result.current.status).toBe('error'));

    healthService.checkBackendHealth.mockResolvedValue({ status: 'ok' });
    act(() => result.current.handleRetry());
    await waitFor(() => expect(result.current.status).toBe('healthy'));
  });

  it('re-checks every 5 minutes in the background without flashing loading', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    healthService.checkBackendHealth.mockResolvedValue({ status: 'ok' });
    const { result, unmount } = setup();
    await waitFor(() => expect(result.current.status).toBe('healthy'));

    healthService.checkBackendHealth.mockResolvedValue({ status: 'down' });
    await act(async () => { await vi.advanceTimersByTimeAsync(300_000); });
    expect(healthService.checkBackendHealth).toHaveBeenCalledTimes(2);
    expect(result.current.status).toBe('error');

    unmount();
    await vi.advanceTimersByTimeAsync(600_000);
    expect(healthService.checkBackendHealth).toHaveBeenCalledTimes(2);
  });
});

describe('alertsService', () => {
  it('maps to the alerts endpoints', async () => {
    api.get.mockResolvedValueOnce({ data: { unread_count: 4 } }).mockResolvedValueOnce({ data: [{ id: 1 }] });
    api.patch.mockResolvedValue({ data: { id: 1, read: false } });
    expect(await alertsService.getUnreadCount()).toBe(4);
    expect(await alertsService.list()).toEqual([{ id: 1 }]);
    expect(api.get).toHaveBeenLastCalledWith('/api/alerts', { params: { limit: 50 } });
    await alertsService.markRead(1, false);
    expect(api.patch).toHaveBeenCalledWith('/api/alerts/1', { read: false });
    await alertsService.markAllRead();
    expect(api.patch).toHaveBeenLastCalledWith('/api/alerts');
    await alertsService.deleteAll();
    expect(api.delete).toHaveBeenCalledWith('/api/alerts');
  });
});

describe('settingsService', () => {
  it.each([
    ['getApiKeys', '/api/apikeys/is_active'],
    ['getModules', '/api/settings/modules'],
    ['getGeneralSettings', '/api/settings/general'],
    ['getNewsfeedList', '/api/settings/modules/newsfeed'],
    ['getAiSettings', '/api/settings/ai'],
    ['getAvailableModels', '/api/settings/ai/available-models'],
  ])('%s GETs %s and unwraps data', async (fn, url) => {
    api.get.mockResolvedValue({ data: { ok: fn } });
    expect(await settingsService[fn]()).toEqual({ ok: fn });
    expect(api.get).toHaveBeenCalledWith(url);
  });
});
