import { act, renderHook, waitFor } from '@testing-library/react';
import {
  useActiveScans, ACTIVE_SCANS_POLL_INTERVAL_MS, ACTIVE_SCANS_IDLE_POLL_INTERVAL_MS,
} from './useActiveScans';
import { activityService } from '../../services/api/activityService';
import { SCAN_LIFECYCLE_EVENT, announceScanLifecycle } from '../../utils/scanLifecycleEvent';

vi.mock('../../services/api/activityService', () => ({ activityService: { listActive: vi.fn() } }));

const RUN = { feature: 'amass', id: 1, target: 'example.com', status: 'running', timestamp: new Date().toISOString() };

beforeEach(() => vi.useFakeTimers({ shouldAdvanceTime: true }));
afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

async function advance(ms) {
  await act(async () => { await vi.advanceTimersByTimeAsync(ms); });
}

describe('useActiveScans', () => {
  it('polls rarely while nothing is running', async () => {
    activityService.listActive.mockResolvedValue([]);
    renderHook(() => useActiveScans());
    await waitFor(() => expect(activityService.listActive).toHaveBeenCalledTimes(1));

    await advance(ACTIVE_SCANS_POLL_INTERVAL_MS * 3);
    expect(activityService.listActive).toHaveBeenCalledTimes(1);

    await advance(ACTIVE_SCANS_IDLE_POLL_INTERVAL_MS - ACTIVE_SCANS_POLL_INTERVAL_MS * 3);
    expect(activityService.listActive).toHaveBeenCalledTimes(2);
  });

  it('polls fast while a scan is unfinished', async () => {
    activityService.listActive.mockResolvedValue([RUN]);
    const { result } = renderHook(() => useActiveScans());
    await waitFor(() => expect(result.current.runs).toHaveLength(1));

    await advance(ACTIVE_SCANS_POLL_INTERVAL_MS);
    expect(activityService.listActive).toHaveBeenCalledTimes(2);
  });

  it('refreshes at once when a scan in this tab starts, without waiting for the idle poll', async () => {
    activityService.listActive.mockResolvedValueOnce([]).mockResolvedValue([RUN]);
    const { result } = renderHook(() => useActiveScans());
    await waitFor(() => expect(activityService.listActive).toHaveBeenCalledTimes(1));

    act(() => { announceScanLifecycle('started'); });

    await waitFor(() => expect(result.current.runs).toHaveLength(1));
  });

  it('announces start, queue/slot changes and terminal events, but not progress', () => {
    const listener = vi.fn();
    window.addEventListener(SCAN_LIFECYCLE_EVENT, listener);
    announceScanLifecycle('progress');
    announceScanLifecycle('queued');
    announceScanLifecycle('running');
    announceScanLifecycle('completed');
    window.removeEventListener(SCAN_LIFECYCLE_EVENT, listener);
    expect(listener).toHaveBeenCalledTimes(3);
  });

  it('keeps the newest response when refreshes overlap and an older one lands last', async () => {
    let resolveOld;
    activityService.listActive
      .mockImplementationOnce(() => new Promise((resolve) => { resolveOld = resolve; }))
      .mockResolvedValueOnce([]);
    const { result } = renderHook(() => useActiveScans());

    // A newer refresh (scan just finished) answers before the slow initial one.
    act(() => { announceScanLifecycle('completed'); });
    await waitFor(() => expect(activityService.listActive).toHaveBeenCalledTimes(2));

    await act(async () => { resolveOld([RUN]); });

    expect(result.current.runs).toEqual([]);
  });
});

