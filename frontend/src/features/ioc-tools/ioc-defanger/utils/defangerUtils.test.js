import { getTypeColor, createFallbackResults } from './defangerUtils';

describe('getTypeColor', () => {
  it('returns the mapped color for a known type', () => {
    expect(getTypeColor('IP Address')).toBe('primary');
    expect(getTypeColor('URL')).toBe('success');
  });

  it('returns "default" for an unknown type', () => {
    expect(getTypeColor('Not A Real Type')).toBe('default');
  });
});

describe('createFallbackResults', () => {
  it('splits input into one unchanged, unprocessed entry per non-blank line', () => {
    const results = createFallbackResults('1.2.3.4\nexample.com');

    expect(results).toEqual([
      { original: '1.2.3.4', processed: '1.2.3.4', types: ['Unknown'], changed: false },
      { original: 'example.com', processed: 'example.com', types: ['Unknown'], changed: false },
    ]);
  });

  it('drops blank lines', () => {
    const results = createFallbackResults('1.2.3.4\n\n   \nexample.com');
    expect(results).toHaveLength(2);
  });

  it('handles CRLF line endings', () => {
    const results = createFallbackResults('1.2.3.4\r\nexample.com');
    expect(results.map((r) => r.original)).toEqual(['1.2.3.4', 'example.com']);
  });

  it('returns an empty array for blank input', () => {
    expect(createFallbackResults('   \n  ')).toEqual([]);
  });
});
