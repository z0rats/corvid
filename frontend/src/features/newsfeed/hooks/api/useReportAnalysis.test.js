import { act, renderHook, waitFor } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { applyEvent, useReportAnalysis } from './useReportAnalysis';
import { reportAnalysisStateAtom, REPORT_ANALYSIS_INITIAL_STATE } from '../../state/reportAnalysisAtoms';
import { openSseStream } from '../../../../core/services/sseStream';

vi.mock('../../../../core/services/sseStream', async (importOriginal) => ({
  ...(await importOriginal()),
  openSseStream: vi.fn(),
}));

// A server-side stream the test pushes frames into; `signal` is the one the hook
// passed to `openSseStream`, so a test can see whether the connection was closed.
function pushableStream() {
  const encoder = new TextEncoder();
  let controller;
  const stream = new ReadableStream({ start(c) { controller = c; } });
  return {
    stream,
    emit: (event) => controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`)),
    end: () => controller.close(),
    fail: () => controller.error(new Error('connection dropped')),
  };
}

let server;
let signals;
let harness;

function setup() {
  harness = renderHook(() => {
    const reportAnalysis = useReportAnalysis();
    const setState = useSetAtom(reportAnalysisStateAtom);
    return { ...reportAnalysis, setState };
  });
  act(() => {
    harness.result.current.setState(REPORT_ANALYSIS_INITIAL_STATE);
  });
  return harness;
}

async function start(result) {
  await act(async () => { result.current.startAnalysis(); });
}

beforeEach(() => {
  signals = [];
  openSseStream.mockImplementation(async (path, { signal }) => {
    server = pushableStream();
    signals.push(signal);
    return server.stream;
  });
});

afterEach(() => {
  act(() => {
    harness?.result.current.stopAnalysis();
  });
  vi.clearAllMocks();
});

describe('applyEvent', () => {
  const prev = { ...REPORT_ANALYSIS_INITIAL_STATE, step: 1, isLoading: true };

  it('applies a "ranking" event', () => {
    expect(applyEvent(prev, { type: 'ranking', articles: [{ id: 1 }], info: 'ranked' })).toMatchObject({
      step: 3, ranking: [{ id: 1 }], infoMessage: 'ranked',
    });
  });

  it('appends each "analysis" article_result, and still advances without one', () => {
    const once = applyEvent(prev, { type: 'analysis', article_result: { id: 1 } });
    expect(applyEvent(once, { type: 'analysis', article_result: { id: 2 } }).analysisResults).toEqual([{ id: 1 }, { id: 2 }]);
    expect(applyEvent(prev, { type: 'analysis' })).toMatchObject({ step: 4, analysisResults: [] });
  });

  it('marks completion on "complete" and ignores unknown types', () => {
    expect(applyEvent(prev, { type: 'complete', message: 'Done' })).toMatchObject({ step: 5, isLoading: false, infoMessage: 'Done' });
    expect(applyEvent(prev, { type: 'something-unexpected' })).toBe(prev);
  });
});

describe('useReportAnalysis — streaming', () => {
  it('opens an authenticated GET stream and resets state to step 1', async () => {
    const { result } = setup();
    await start(result);

    expect(openSseStream).toHaveBeenCalledWith('/api/newsfeed/analysis/top-articles/stream', {
      method: 'GET', signal: expect.any(AbortSignal),
    });
    expect(result.current.step).toBe(1);
    expect(result.current.isLoading).toBe(true);
  });

  it('applies streamed events, then closes the connection on "complete"', async () => {
    const { result } = setup();
    await start(result);

    await act(async () => {
      server.emit({ type: 'ranking', articles: [{ id: 1 }] });
      server.emit({ type: 'analysis', article_result: { id: 1 } });
      server.emit({ type: 'complete', message: 'Done' });
    });

    await waitFor(() => expect(result.current.step).toBe(5));
    expect(result.current.ranking).toEqual([{ id: 1 }]);
    expect(result.current.analysisResults).toEqual([{ id: 1 }]);
    expect(result.current.isLoading).toBe(false);
    expect(signals[0].aborted).toBe(true);
  });

  it('sets a clean error when the connection drops', async () => {
    const { result } = setup();
    await start(result);

    await act(async () => { server.fail(); });

    await waitFor(() => expect(result.current.error).toBe('An error occurred while streaming data.'));
    expect(result.current.isLoading).toBe(false);
    expect(result.current.step).toBe(0);
  });

  it('treats a stream that ends without "complete" as an error, not an endless spinner', async () => {
    const { result } = setup();
    await start(result);

    await act(async () => { server.end(); });

    await waitFor(() => expect(result.current.error).toBe('An error occurred while streaming data.'));
  });

  it('sets the error when the stream cannot be opened (e.g. 401)', async () => {
    openSseStream.mockRejectedValueOnce(new Error('Server error: Unauthorized'));
    const { result } = setup();
    await start(result);

    expect(result.current.error).toBe('An error occurred while streaming data.');
  });

  it('closes a still-open previous stream when starting a new one', async () => {
    const { result } = setup();
    await start(result);
    await start(result);

    expect(signals[0].aborted).toBe(true);
    expect(signals[1].aborted).toBe(false);
  });
});

describe('useReportAnalysis — stopAnalysis', () => {
  it('closes the active stream and resets to the idle step, without reporting an error', async () => {
    const { result } = setup();
    await start(result);

    act(() => { result.current.stopAnalysis(); });

    expect(signals[0].aborted).toBe(true);
    expect(result.current.step).toBe(0);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.infoMessage).toBe('Analysis stream stopped by user.');
  });

  it('is a no-op on the stream side when nothing is running', () => {
    const { result } = setup();

    expect(() => act(() => { result.current.stopAnalysis(); })).not.toThrow();
    expect(result.current.step).toBe(0);
  });
});

describe('useReportAnalysis — showStopButton', () => {
  it('is true only while a stream is actively running (steps 1-4)', async () => {
    const { result } = setup();
    expect(result.current.showStopButton).toBe(false);

    await start(result);
    expect(result.current.showStopButton).toBe(true);

    await act(async () => { server.emit({ type: 'complete', message: 'Done' }); });
    await waitFor(() => expect(result.current.showStopButton).toBe(false));
  });
});
