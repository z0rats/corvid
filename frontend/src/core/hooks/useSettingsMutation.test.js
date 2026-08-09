import { act, renderHook } from '@testing-library/react';
import { useSettingsMutation } from './useSettingsMutation';

describe('useSettingsMutation', () => {
  it('starts idle, with loading false and error null', () => {
    const { result } = renderHook(() => useSettingsMutation());
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('run merges the resolved success payload into { success: true, ... }', async () => {
    const { result } = renderHook(() => useSettingsMutation());
    const asyncFn = vi.fn().mockResolvedValue({ message: 'saved' });

    let outcome;
    await act(async () => {
      outcome = await result.current.run(asyncFn, 'fallback');
    });

    expect(outcome).toEqual({ success: true, message: 'saved' });
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('run sets error to the response detail when present, and returns { success: false, message }', async () => {
    const err = { response: { data: { detail: 'server said no' } } };
    const asyncFn = vi.fn().mockRejectedValue(err);
    const { result } = renderHook(() => useSettingsMutation());

    let outcome;
    await act(async () => {
      outcome = await result.current.run(asyncFn, 'fallback message');
    });

    expect(outcome).toEqual({ success: false, message: 'server said no' });
    expect(result.current.error).toBe('server said no');
  });

  it('run falls back to errorFallback when the error has no response detail', async () => {
    const asyncFn = vi.fn().mockRejectedValue(new Error('network down'));
    const { result } = renderHook(() => useSettingsMutation());

    let outcome;
    await act(async () => {
      outcome = await result.current.run(asyncFn, 'fallback message');
    });

    expect(outcome).toEqual({ success: false, message: 'fallback message' });
  });

  it('is true while an operation is in flight and false once it settles', async () => {
    let resolveFn;
    const asyncFn = vi.fn(() => new Promise((resolve) => { resolveFn = resolve; }));
    const { result } = renderHook(() => useSettingsMutation());

    let runPromise;
    act(() => {
      runPromise = result.current.run(asyncFn, 'fallback');
    });
    expect(result.current.loading).toBe(true);

    await act(async () => {
      resolveFn({ message: 'done' });
      await runPromise;
    });
    expect(result.current.loading).toBe(false);
  });

  it('clears a previous error at the start of the next run', async () => {
    const { result } = renderHook(() => useSettingsMutation());

    await act(async () => {
      await result.current.run(vi.fn().mockRejectedValue(new Error('boom')), 'fallback');
    });
    expect(result.current.error).toBe('fallback');

    await act(async () => {
      await result.current.run(vi.fn().mockResolvedValue({ message: 'ok' }), 'fallback');
    });
    expect(result.current.error).toBeNull();
  });
});
