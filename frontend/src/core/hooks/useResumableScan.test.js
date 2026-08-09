import { failedReduce, buildRunningSeed } from './useResumableScan';

describe('failedReduce', () => {
  it('sets phase to failed and carries the event error', () => {
    const prev = { phase: 'running', searchId: 'abc', checked: 3 };
    expect(failedReduce(prev, { error: 'boom', search_id: 'abc' })).toEqual({
      phase: 'failed', searchId: 'abc', checked: 3, error: 'boom',
    });
  });

  it('falls back to the previous searchId when the event carries none', () => {
    const prev = { phase: 'running', searchId: 'abc' };
    expect(failedReduce(prev, { error: 'lost connection' }).searchId).toBe('abc');
  });
});

describe('buildRunningSeed', () => {
  it('merges initialState, phase: running, and the extra fields', () => {
    expect(buildRunningSeed({ phase: 'idle', foundSites: [] }, { username: 'alice' })).toEqual({
      phase: 'running', foundSites: [], username: 'alice',
    });
  });

  it('lets extra fields override initialState', () => {
    expect(buildRunningSeed({ phase: 'idle', username: '' }, { username: 'bob' }).username).toBe('bob');
  });
});
