import { act, renderHook } from '@testing-library/react';
import { useAsyncOperation, useAsyncOperationWithRetry } from './useAsyncOperation';

describe('useAsyncOperation', () => {
  it('sets isLoading during the operation and clears it after', async () => {
    const { result } = renderHook(() => useAsyncOperation());
    let resolveOp;
    const op = () => new Promise((resolve) => { resolveOp = resolve; });

    let promise;
    act(() => {
      promise = result.current.executeAsync(op);
    });
    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolveOp('done');
      await promise;
    });

    expect(result.current.isLoading).toBe(false);
  });

  it('returns the operation result on success', async () => {
    const { result } = renderHook(() => useAsyncOperation());

    let returned;
    await act(async () => {
      returned = await result.current.executeAsync(async () => 'the result');
    });

    expect(returned).toBe('the result');
    expect(result.current.error).toBeNull();
  });

  it('sets the error message and rethrows on failure', async () => {
    const { result } = renderHook(() => useAsyncOperation());

    let caught;
    await act(async () => {
      try {
        await result.current.executeAsync(async () => {
          throw new Error('operation failed');
        });
      } catch (err) {
        caught = err;
      }
    });

    expect(caught.message).toBe('operation failed');
    expect(result.current.error).toBe('operation failed');
    expect(result.current.isLoading).toBe(false);
  });

  it('falls back to a generic message when the error has none', async () => {
    const { result } = renderHook(() => useAsyncOperation());

    await act(async () => {
      try {
        await result.current.executeAsync(async () => {
          throw new Error();
        });
      } catch {
        // expected
      }
    });

    expect(result.current.error).toBe('Unknown error occurred');
  });

  it('clearError resets the error to null', async () => {
    const { result } = renderHook(() => useAsyncOperation());
    await act(async () => {
      try {
        await result.current.executeAsync(async () => {
          throw new Error('x');
        });
      } catch {
        // expected
      }
    });

    act(() => result.current.clearError());

    expect(result.current.error).toBeNull();
  });

  it('reset clears both loading and error state', async () => {
    const { result } = renderHook(() => useAsyncOperation());
    await act(async () => {
      try {
        await result.current.executeAsync(async () => {
          throw new Error('x');
        });
      } catch {
        // expected
      }
    });

    act(() => result.current.reset());

    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });
});

describe('useAsyncOperationWithRetry', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('returns the result on the first attempt without retrying', async () => {
    const { result } = renderHook(() => useAsyncOperationWithRetry(3, 100));
    const op = vi.fn().mockResolvedValue('ok');

    let returned;
    await act(async () => {
      returned = await result.current.executeWithRetry(op);
    });

    expect(returned).toBe('ok');
    expect(op).toHaveBeenCalledTimes(1);
    expect(result.current.retryCount).toBe(0);
  });

  it('retries on failure and succeeds on a later attempt', async () => {
    const { result } = renderHook(() => useAsyncOperationWithRetry(3, 100));
    const op = vi.fn().mockRejectedValueOnce(new Error('fail once')).mockResolvedValueOnce('ok');

    let promise;
    act(() => {
      promise = result.current.executeWithRetry(op);
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
      await promise;
    });

    expect(op).toHaveBeenCalledTimes(2);
  });

  it('throws the last error once maxRetries is exhausted', async () => {
    const { result } = renderHook(() => useAsyncOperationWithRetry(2, 10));
    const op = vi.fn().mockRejectedValue(new Error('always fails'));

    let promise;
    let caught;
    act(() => {
      promise = result.current.executeWithRetry(op).catch((err) => {
        caught = err;
      });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
      await promise;
    });

    expect(op).toHaveBeenCalledTimes(3); // initial attempt + 2 retries
    expect(caught.message).toBe('always fails');
  });
});
