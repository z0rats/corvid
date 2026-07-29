import { act, renderHook, waitFor } from '@testing-library/react';
import { useRemoteConfig } from './useRemoteConfig';

const DEFAULT_CONFIG = { foo: 'bar' };

describe('useRemoteConfig', () => {
  it('starts with the default config and loading true before getFn resolves', () => {
    const getFn = vi.fn(() => new Promise(() => {}));
    const updateFn = vi.fn();

    const { result } = renderHook(() => useRemoteConfig(getFn, updateFn, DEFAULT_CONFIG));

    expect(result.current.config).toBe(DEFAULT_CONFIG);
    expect(result.current.loading).toBe(true);
  });

  it('loads config on mount and calls getFn exactly once', async () => {
    const remoteConfig = { foo: 'baz' };
    const getFn = vi.fn().mockResolvedValue(remoteConfig);
    const updateFn = vi.fn();

    const { result } = renderHook(() => useRemoteConfig(getFn, updateFn, DEFAULT_CONFIG));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.config).toEqual(remoteConfig);
    expect(getFn).toHaveBeenCalledTimes(1);
  });

  it('sets error and stops loading when getFn rejects', async () => {
    const err = new Error('load failed');
    const getFn = vi.fn().mockRejectedValue(err);
    const updateFn = vi.fn();

    const { result } = renderHook(() => useRemoteConfig(getFn, updateFn, DEFAULT_CONFIG));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe(err);
  });

  it('updateConfig merges updates into config and calls updateFn with the merge result', async () => {
    const getFn = vi.fn().mockResolvedValue({ foo: 'bar', count: 1 });
    const updatedConfig = { foo: 'bar', count: 2 };
    const updateFn = vi.fn().mockResolvedValue(updatedConfig);

    const { result } = renderHook(() => useRemoteConfig(getFn, updateFn, DEFAULT_CONFIG));
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.updateConfig({ count: 2 });
    });

    expect(updateFn).toHaveBeenCalledWith({ foo: 'bar', count: 2 });
    expect(result.current.config).toEqual(updatedConfig);
  });

  it('updateConfig returns { success: false } and does not call updateFn again while a save is in flight', async () => {
    const getFn = vi.fn().mockResolvedValue(DEFAULT_CONFIG);
    let resolveUpdate;
    const updateFn = vi.fn(() => new Promise((resolve) => { resolveUpdate = resolve; }));

    const { result } = renderHook(() => useRemoteConfig(getFn, updateFn, DEFAULT_CONFIG));
    await waitFor(() => expect(result.current.loading).toBe(false));

    let firstCallPromise;
    act(() => {
      firstCallPromise = result.current.updateConfig({ foo: 'first' });
    });

    let secondResult;
    await act(async () => {
      secondResult = await result.current.updateConfig({ foo: 'second' });
    });

    expect(secondResult).toEqual({ success: false });
    expect(updateFn).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveUpdate({ foo: 'first' });
      await firstCallPromise;
    });
  });

  it('does not throw or warn when unmounted before getFn resolves', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    let resolveGet;
    const getFn = vi.fn(() => new Promise((resolve) => { resolveGet = resolve; }));
    const updateFn = vi.fn();

    const { unmount } = renderHook(() => useRemoteConfig(getFn, updateFn, DEFAULT_CONFIG));

    unmount();
    await act(async () => {
      resolveGet(DEFAULT_CONFIG);
    });

    expect(consoleError).not.toHaveBeenCalled();
    consoleError.mockRestore();
  });
});
