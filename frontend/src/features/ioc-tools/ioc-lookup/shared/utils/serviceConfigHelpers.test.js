import { scoreTlpMapper, withErrorHandling, withNoDataCheck } from './serviceConfigHelpers';

describe('withErrorHandling', () => {
  it('returns an error summary with WHITE tlp when responseData has an error', () => {
    const wrapped = withErrorHandling(() => ({ summary: 'unused', tlp: 'RED' }));

    expect(wrapped({ error: 'boom', message: 'Something broke' })).toEqual({
      summary: 'Error: Something broke',
      tlp: 'WHITE',
    });
  });

  it('falls back to the error field itself when message is missing', () => {
    const wrapped = withErrorHandling(() => ({ summary: 'unused', tlp: 'RED' }));

    expect(wrapped({ error: 'boom' })).toEqual({ summary: 'Error: boom', tlp: 'WHITE' });
  });

  it('delegates to the wrapped function when there is no error', () => {
    const wrapped = withErrorHandling((data) => ({ summary: `ok:${data.value}`, tlp: 'GREEN' }));

    expect(wrapped({ value: 42 })).toEqual({ summary: 'ok:42', tlp: 'GREEN' });
  });
});

describe('withNoDataCheck', () => {
  it('returns a no-data summary when the target field is missing', () => {
    const wrapped = withNoDataCheck(() => ({ summary: 'unused', tlp: 'GREEN' }), 'results');

    expect(wrapped({})).toEqual({ summary: 'No data available', tlp: 'WHITE' });
  });

  it('returns a no-data summary when the target field is falsy (empty string)', () => {
    const wrapped = withNoDataCheck(() => ({ summary: 'unused', tlp: 'GREEN' }), 'results');

    expect(wrapped({ results: '' })).toEqual({ summary: 'No data available', tlp: 'WHITE' });
  });

  it('treats an empty array as present data - only falsy values count as "no data"', () => {
    // [] is truthy in JS, so a target of [] does NOT trip the no-data check.
    const wrapped = withNoDataCheck((data) => ({ summary: `count:${data.results.length}`, tlp: 'GREEN' }), 'results');

    expect(wrapped({ results: [] })).toEqual({ summary: 'count:0', tlp: 'GREEN' });
  });

  it('delegates to the wrapped function when the target field is present', () => {
    const wrapped = withNoDataCheck((data) => ({ summary: `count:${data.results.length}`, tlp: 'GREEN' }), 'results');

    expect(wrapped({ results: [1, 2] })).toEqual({ summary: 'count:2', tlp: 'GREEN' });
  });

  it('checks the whole responseData when no path is given', () => {
    const wrapped = withNoDataCheck(() => ({ summary: 'ok', tlp: 'GREEN' }));

    expect(wrapped(null)).toEqual({ summary: 'No data available', tlp: 'WHITE' });
    expect(wrapped({ anything: true })).toEqual({ summary: 'ok', tlp: 'GREEN' });
  });
});

describe('scoreTlpMapper', () => {
  it('returns RED at or above the red threshold', () => {
    expect(scoreTlpMapper(75)).toBe('RED');
    expect(scoreTlpMapper(100)).toBe('RED');
  });

  it('returns AMBER at or above the amber threshold but below red', () => {
    expect(scoreTlpMapper(25)).toBe('AMBER');
    expect(scoreTlpMapper(74)).toBe('AMBER');
  });

  it('returns GREEN below the amber threshold', () => {
    expect(scoreTlpMapper(0)).toBe('GREEN');
    expect(scoreTlpMapper(24)).toBe('GREEN');
  });

  it('respects custom thresholds', () => {
    expect(scoreTlpMapper(50, { red: 90, amber: 50 })).toBe('AMBER');
    expect(scoreTlpMapper(49, { red: 90, amber: 50 })).toBe('GREEN');
  });
});
