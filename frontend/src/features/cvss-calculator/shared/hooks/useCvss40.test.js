import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useCvss40 } from './useCvss40';
import { cvss40Atom, CVSS40_INITIAL } from '../state/cvssAtoms';
import api from '../../../../core/services/baseApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { post: vi.fn() },
}));

// cvss40Atom is module-scoped, so it doesn't reset between tests on its own -
// every test below resets it explicitly via this harness.
function useTestHarness() {
  const cvss40 = useCvss40();
  const setState = useSetAtom(cvss40Atom);
  return { ...cvss40, setState };
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe('useCvss40 — updateMetric', () => {
  it('does not call the backend before the debounce delay elapses', () => {
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS40_INITIAL));

    act(() => result.current.updateMetric('base', 'attack_vector', 'N'));

    expect(api.post).not.toHaveBeenCalled();
  });

  it('debounces rapid edits into a single backend call', async () => {
    api.post.mockResolvedValue({ data: { base_score: 9.3, base_severity: 'Critical', vector_string: 'x' } });
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS40_INITIAL));

    act(() => result.current.updateMetric('base', 'attack_vector', 'N'));
    act(() => vi.advanceTimersByTime(200));
    act(() => result.current.updateMetric('base', 'attack_vector', 'A'));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(api.post).toHaveBeenCalledTimes(1);
  });

  it('stores the returned scores and vector string, and turns loading off', async () => {
    api.post.mockResolvedValue({
      data: { base_score: 9.3, base_severity: 'Critical', vector_string: 'CVSS:4.0/AV:N/...' },
    });
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS40_INITIAL));

    act(() => result.current.updateMetric('base', 'attack_vector', 'N'));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(result.current.state.scores.base_score).toBe(9.3);
    expect(result.current.state.scores.base_severity).toBe('Critical');
    expect(result.current.state.vectorString).toBe('CVSS:4.0/AV:N/...');
    expect(result.current.state.loading).toBe(false);
  });

  it('falls back to the base score/severity when the backend omits threat/environmental scores', async () => {
    api.post.mockResolvedValue({
      data: { base_score: 7.1, base_severity: 'High', vector_string: 'x' },
    });
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS40_INITIAL));

    act(() => result.current.updateMetric('base', 'attack_vector', 'N'));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(result.current.state.scores.threat_score).toBe(7.1);
    expect(result.current.state.scores.threat_severity).toBe('High');
    expect(result.current.state.scores.environmental_score).toBe(7.1);
  });

  it('surfaces the backend error detail and turns loading off', async () => {
    api.post.mockRejectedValue({ response: { data: { detail: 'Invalid CVSS 4.0 metrics' } } });
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS40_INITIAL));

    act(() => result.current.updateMetric('base', 'attack_vector', 'N'));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(result.current.state.error).toBe('Invalid CVSS 4.0 metrics');
    expect(result.current.state.loading).toBe(false);
  });
});

describe('useCvss40 — updateSingleMetric', () => {
  it('routes a modified_-prefixed metric into environmental', () => {
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS40_INITIAL));

    act(() => result.current.updateSingleMetric('modified_attack_vector', 'N'));

    expect(result.current.state.metrics.environmental.modified_attack_vector).toBe('N');
  });

  it('routes a known supplemental metric into supplemental', () => {
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS40_INITIAL));

    act(() => result.current.updateSingleMetric('safety', 'P'));

    expect(result.current.state.metrics.supplemental.safety).toBe('P');
  });

  it('routes exploit_maturity into threat', () => {
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS40_INITIAL));

    act(() => result.current.updateSingleMetric('exploit_maturity', 'A'));

    expect(result.current.state.metrics.threat.exploit_maturity).toBe('A');
  });

  it('routes anything else into base', () => {
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS40_INITIAL));

    act(() => result.current.updateSingleMetric('attack_vector', 'A'));

    expect(result.current.state.metrics.base.attack_vector).toBe('A');
  });
});

describe('useCvss40 — resetState', () => {
  it('restores the initial state and cancels a pending debounced fetch', async () => {
    api.post.mockResolvedValue({ data: { base_score: 1, base_severity: 'Low', vector_string: 'x' } });
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(CVSS40_INITIAL));

    act(() => result.current.updateMetric('base', 'attack_vector', 'A'));
    act(() => result.current.resetState());

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(api.post).not.toHaveBeenCalled();
    expect(result.current.state.metrics.base.attack_vector).toBe('N');
  });
});
