import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useReportAnalysis } from './useReportAnalysis';
import { reportAnalysisStateAtom, REPORT_ANALYSIS_INITIAL_STATE } from '../../state/reportAnalysisAtoms';
import { getStreamUrl } from '../../utils/urlUtils';

vi.mock('../../utils/urlUtils');

// This is the one place in the app that drives a raw browser EventSource
// (every other scan-style feature goes through core/hooks/useResumableScan's
// fetch-stream instead) - jsdom doesn't implement EventSource, so tests stand
// one in for the browser global rather than mocking this hook away.
class FakeEventSource {
  constructor(url) {
    this.url = url;
    this.closed = false;
    this.onmessage = null;
    this.onerror = null;
    FakeEventSource.instances.push(this);
  }

  emit(data) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  emitRaw(rawData) {
    this.onmessage?.({ data: rawData });
  }

  emitError() {
    this.onerror?.();
  }

  close() {
    this.closed = true;
  }
}
FakeEventSource.instances = [];

// reportAnalysisStateAtom and the hook's `activeEventSource` are both
// module-scoped, so neither resets between tests on its own - every test
// resets the atom explicitly, and the shared `afterEach` below closes
// whatever stream a test left open so it can't leak into the next one.
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

beforeEach(() => {
  FakeEventSource.instances = [];
  global.EventSource = FakeEventSource;
  getStreamUrl.mockReturnValue('https://example.test/api/newsfeed/analysis/top-articles/stream');
});

afterEach(() => {
  act(() => {
    harness?.result.current.stopAnalysis();
  });
  vi.clearAllMocks();
});

describe('useReportAnalysis — startAnalysis', () => {
  it('opens an EventSource against the stream URL and resets state to step 1', () => {
    const { result } = setup();

    act(() => { result.current.startAnalysis(); });

    expect(FakeEventSource.instances).toHaveLength(1);
    expect(FakeEventSource.instances[0].url).toBe(
      'https://example.test/api/newsfeed/analysis/top-articles/stream',
    );
    expect(result.current.step).toBe(1);
    expect(result.current.isLoading).toBe(true);
  });

  it('applies a "ranking" event to state', () => {
    const { result } = setup();
    act(() => { result.current.startAnalysis(); });

    act(() => {
      FakeEventSource.instances[0].emit({ type: 'ranking', articles: [{ id: 1 }], info: 'ranked 10 articles' });
    });

    expect(result.current.step).toBe(3);
    expect(result.current.ranking).toEqual([{ id: 1 }]);
    expect(result.current.infoMessage).toBe('ranked 10 articles');
  });

  it('appends each "analysis" event\'s article_result and advances to step 4', () => {
    const { result } = setup();
    act(() => { result.current.startAnalysis(); });

    act(() => {
      FakeEventSource.instances[0].emit({ type: 'analysis', article_result: { id: 1, summary: 'a' } });
    });
    act(() => {
      FakeEventSource.instances[0].emit({ type: 'analysis', article_result: { id: 2, summary: 'b' } });
    });

    expect(result.current.step).toBe(4);
    expect(result.current.analysisResults).toEqual([
      { id: 1, summary: 'a' },
      { id: 2, summary: 'b' },
    ]);
  });

  it('advances to step 4 on an "analysis" event with no article_result', () => {
    const { result } = setup();
    act(() => { result.current.startAnalysis(); });

    act(() => {
      FakeEventSource.instances[0].emit({ type: 'analysis' });
    });

    expect(result.current.step).toBe(4);
    expect(result.current.analysisResults).toEqual([]);
  });

  it('closes the stream and marks completion on a "complete" event', () => {
    const { result } = setup();
    act(() => { result.current.startAnalysis(); });
    const es = FakeEventSource.instances[0];

    act(() => { es.emit({ type: 'complete', message: 'Done' }); });

    expect(result.current.step).toBe(5);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.infoMessage).toBe('Done');
    expect(es.closed).toBe(true);
  });

  it('ignores blank messages and unknown event types without throwing', () => {
    const { result } = setup();
    act(() => { result.current.startAnalysis(); });
    const es = FakeEventSource.instances[0];

    act(() => { es.emitRaw(''); });
    act(() => { es.emit({ type: 'something-unexpected' }); });

    expect(result.current.step).toBe(1);
  });

  it('sets a clean error and closes the stream when the connection itself errors', () => {
    const { result } = setup();
    act(() => { result.current.startAnalysis(); });
    const es = FakeEventSource.instances[0];

    act(() => { es.emitError(); });

    expect(result.current.error).toBe('An error occurred while streaming data.');
    expect(result.current.isLoading).toBe(false);
    expect(result.current.step).toBe(0);
    expect(es.closed).toBe(true);
  });

  it('closes a still-open previous stream when starting a new one', () => {
    const { result } = setup();
    act(() => { result.current.startAnalysis(); });
    const first = FakeEventSource.instances[0];

    act(() => { result.current.startAnalysis(); });

    expect(first.closed).toBe(true);
    expect(FakeEventSource.instances).toHaveLength(2);
  });
});

describe('useReportAnalysis — stopAnalysis', () => {
  it('closes the active stream and resets to the idle step', () => {
    const { result } = setup();
    act(() => { result.current.startAnalysis(); });
    const es = FakeEventSource.instances[0];

    act(() => { result.current.stopAnalysis(); });

    expect(es.closed).toBe(true);
    expect(result.current.step).toBe(0);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.infoMessage).toBe('Analysis stream stopped by user.');
  });

  it('is a no-op on the stream side when nothing is running', () => {
    const { result } = setup();

    expect(() => act(() => { result.current.stopAnalysis(); })).not.toThrow();
    expect(result.current.step).toBe(0);
  });
});

describe('useReportAnalysis — showStopButton', () => {
  it('is true only while a stream is actively running (steps 1-4)', () => {
    const { result } = setup();

    expect(result.current.showStopButton).toBe(false);

    act(() => { result.current.startAnalysis(); });
    expect(result.current.showStopButton).toBe(true);

    act(() => { FakeEventSource.instances[0].emit({ type: 'complete', message: 'Done' }); });
    expect(result.current.showStopButton).toBe(false);
  });
});
