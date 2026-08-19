import { renderHook, act } from '@testing-library/react';
import { useDebounce } from './useDebounce';

describe('useDebounce', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('delays invoking the callback until the delay has elapsed', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebounce(callback, 500));

    act(() => result.current('a'));
    expect(callback).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(499));
    expect(callback).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(1));
    expect(callback).toHaveBeenCalledWith('a');
  });

  it('resets the timer on each call, only firing once for a burst of calls', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebounce(callback, 500));

    act(() => result.current('a'));
    act(() => vi.advanceTimersByTime(300));
    act(() => result.current('b'));
    act(() => vi.advanceTimersByTime(300));
    expect(callback).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(200));
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('b');
  });

  it('always invokes the latest callback, even if it changed after scheduling', () => {
    const firstCallback = vi.fn();
    const secondCallback = vi.fn();
    const { result, rerender } = renderHook(({ cb }) => useDebounce(cb, 500), {
      initialProps: { cb: firstCallback },
    });

    act(() => result.current('a'));
    rerender({ cb: secondCallback });
    act(() => vi.advanceTimersByTime(500));

    expect(firstCallback).not.toHaveBeenCalled();
    expect(secondCallback).toHaveBeenCalledWith('a');
  });

  it('cancels the pending call on unmount', () => {
    const callback = vi.fn();
    const { result, unmount } = renderHook(() => useDebounce(callback, 500));

    act(() => result.current('a'));
    unmount();
    act(() => vi.advanceTimersByTime(500));

    expect(callback).not.toHaveBeenCalled();
  });
});
