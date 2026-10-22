import { act, renderHook } from '@testing-library/react';
import { useKeyTests } from './useKeyTests';
import { settingsApi } from '../../services/api/settingsApi';

vi.mock('../../services/api/settingsApi');

afterEach(() => vi.clearAllMocks());

function deferred() {
  let resolve;
  const promise = new Promise((r) => { resolve = r; });
  return { promise, resolve };
}

describe('useKeyTests', () => {
  it('stores a single result and clears the in-flight flag', async () => {
    settingsApi.testApiKey.mockResolvedValue({ service: 'shodan', status: 'ok' });
    const { result } = renderHook(() => useKeyTests());

    await act(async () => { await result.current.testService('shodan'); });

    expect(settingsApi.testApiKey).toHaveBeenCalledWith('shodan');
    expect(result.current.results.shodan).toEqual({ service: 'shodan', status: 'ok' });
    expect(result.current.testing.has('shodan')).toBe(false);
  });

  it('turns a failed request into an error result, using a string detail only', async () => {
    settingsApi.testApiKey
      .mockRejectedValueOnce({ response: { data: { detail: 'Unknown service' } } })
      .mockRejectedValueOnce({ response: { data: { detail: [{ msg: 'bad' }] } } });
    const { result } = renderHook(() => useKeyTests());

    await act(async () => { await result.current.testService('a'); });
    await act(async () => { await result.current.testService('b'); });

    expect(result.current.results.a).toEqual({ service: 'a', status: 'error', detail: 'Unknown service' });
    expect(result.current.results.b.status).toBe('error');
    expect(typeof result.current.results.b.detail).toBe('string');
    expect(result.current.results.b.detail).not.toBe('Unknown service');
  });

  it('drops a not_configured answer to the automatic check after a save', async () => {
    settingsApi.testApiKey.mockResolvedValue({ service: 'mandiant', status: 'not_configured' });
    const { result } = renderHook(() => useKeyTests());

    await act(async () => { await result.current.testService('mandiant', { afterSave: true }); });

    expect(result.current.results.mandiant).toBeUndefined();
  });

  it('applies every result of Test all', async () => {
    settingsApi.testAllApiKeys.mockResolvedValue([
      { service: 'shodan', status: 'ok' },
      { service: 'github', status: 'rejected' },
    ]);
    const { result } = renderHook(() => useKeyTests());

    await act(async () => { await result.current.testAll(); });

    expect(result.current.results).toEqual({
      shodan: { service: 'shodan', status: 'ok' },
      github: { service: 'github', status: 'rejected' },
    });
    expect(result.current.testingAll).toBe(false);
  });

  it('keeps the newer single result when an older Test all answers later', async () => {
    const all = deferred();
    settingsApi.testAllApiKeys.mockReturnValue(all.promise);
    settingsApi.testApiKey.mockResolvedValue({ service: 'shodan', status: 'ok' });
    const { result } = renderHook(() => useKeyTests());

    let allDone;
    act(() => { allDone = result.current.testAll(); });
    await act(async () => { await result.current.testService('shodan'); });
    await act(async () => {
      all.resolve([{ service: 'shodan', status: 'rejected' }]);
      await allDone;
    });

    expect(result.current.results.shodan.status).toBe('ok');
  });

  it('reports a failed Test all as an error, not per-service results', async () => {
    settingsApi.testAllApiKeys.mockRejectedValue({ response: { data: { detail: 'Too many requests' } } });
    const { result } = renderHook(() => useKeyTests());

    await act(async () => { await result.current.testAll(); });

    expect(result.current.error).toBe('Too many requests');
    expect(result.current.results).toEqual({});
  });
});
