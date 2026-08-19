import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useCvss31 } from './useCvss31';
import { cvss31Atom, CVSS31_INITIAL } from '../state/cvssAtoms';
import api from '../../../../core/services/baseApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { post: vi.fn() },
}));

// cvss31Atom is module-scoped, so it doesn't reset between tests on its own -
// every test below resets it explicitly via this harness.
function useTestHarness() {
  const cvss31 = useCvss31();
  const setState = useSetAtom(cvss31Atom);
  return { ...cvss31, setState };
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe('useCvss31 — updateMetric', () => {
  it('recalculates scores locally and immediately, without waiting for the debounce', () => {
    const { result } = renderHook(() => useTestHarness());

    act(() => result.current.setState(CVSS31_INITIAL));
    act(() => result.current.updateMetric('base', 'attackVector', 'N'));
    act(() => {
      result.current.updateMetric('base', 'confidentialityImpact', 'H');
      result.current.updateMetric('base', 'integrityImpact', 'H');
      result.current.updateMetric('base', 'availabilityImpact', 'H');
    });

    expect(result.current.state.scores.base.baseScore).toBe(9.8);
    expect(result.current.state.scores.base.baseSeverity).toBe('Critical');
    expect(api.post).not.toHaveBeenCalled();
  });

  it('debounces the backend vector-string fetch to a single call after rapid edits', async () => {
    api.post.mockResolvedValue({ data: { vector_string: 'CVSS:3.1/AV:N/...' } });
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS31_INITIAL));

    act(() => result.current.updateMetric('base', 'attackVector', 'N'));
    act(() => vi.advanceTimersByTime(500));
    act(() => result.current.updateMetric('base', 'attackVector', 'A'));
    act(() => vi.advanceTimersByTime(500));

    expect(api.post).not.toHaveBeenCalled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(api.post).toHaveBeenCalledTimes(1);
  });

  it('stores the vector string returned by the backend and clears any prior error', async () => {
    api.post.mockResolvedValue({ data: { vector_string: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H' } });
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState({ ...CVSS31_INITIAL, error: 'stale error' }));

    act(() => result.current.updateMetric('base', 'attackVector', 'N'));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });

    expect(result.current.state.vectorString).toBe('CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H');
    expect(result.current.state.error).toBeNull();
  });

  it('surfaces the backend error detail and preserves the locally-computed scores', async () => {
    api.post.mockRejectedValue({ response: { data: { detail: 'Invalid CVSS 3.1 metrics' } } });
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS31_INITIAL));

    act(() => result.current.updateMetric('base', 'attackVector', 'N'));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });

    expect(result.current.state.error).toBe('Invalid CVSS 3.1 metrics');
    expect(result.current.state.scores.base.baseScore).toBeDefined();
  });

  it('falls back to a generic error message when the backend gives no detail', async () => {
    api.post.mockRejectedValue(new Error('network down'));
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS31_INITIAL));

    act(() => result.current.updateMetric('base', 'attackVector', 'N'));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });

    expect(result.current.state.error).toBe('network down');
  });
});

describe('useCvss31 — resetState', () => {
  it('restores the initial state and cancels a pending debounced fetch', async () => {
    api.post.mockResolvedValue({ data: { vector_string: 'x' } });
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS31_INITIAL));

    act(() => result.current.updateMetric('base', 'attackVector', 'A'));
    act(() => result.current.resetState());

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });

    expect(api.post).not.toHaveBeenCalled();
    expect(result.current.state.metrics.base.attackVector).toBe('N');
  });
});
