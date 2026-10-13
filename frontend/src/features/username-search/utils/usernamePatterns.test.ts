import {
  expandPattern, isPattern, MAX_PATTERN_SHOWN, MAX_PATTERN_TOTAL, type PatternResult, unescapeLiterals,
} from './usernamePatterns';

type Expanded = Extract<PatternResult, { ok: true }>;
type Rejected = Extract<PatternResult, { ok: false }>;

// The project compiles without strictNullChecks, so `ok` doesn't narrow the union by itself.
const expand = (pattern: string, limit?: number): Expanded => {
  const result = expandPattern(pattern, limit);
  if (!result.ok) {
    const { error, detail } = result as Rejected;
    throw new Error(`expected ok, got ${error}: ${detail ?? ''}`);
  }
  return result as Expanded;
};

describe('isPattern', () => {
  it('recognises an unescaped set and ignores plain or escaped brackets', () => {
    expect(isPattern('john[0-9]')).toBe(true);
    expect(isPattern('johnsmith')).toBe(false);
    expect(isPattern('hello\\[world')).toBe(false);
  });

  it('reads an escaped backslash before a set as a pattern, like the parser does', () => {
    expect(isPattern('john\\\\[ab]')).toBe(true);
  });
});

describe('unescapeLiterals', () => {
  it('turns escaped brackets and backslashes back into the literal characters', () => {
    expect(unescapeLiterals('john\\[x\\]')).toBe('john[x]');
    expect(unescapeLiterals('a\\\\b')).toBe('a\\b');
    expect(unescapeLiterals('plain_handle')).toBe('plain_handle');
  });
});

describe('expandPattern', () => {
  it('expands character sets and ranges in order', () => {
    expect(expand('john[abc]').values).toEqual(['johna', 'johnb', 'johnc']);
    expect(expand('user[0-3]').values).toEqual(['user0', 'user1', 'user2', 'user3']);
    expect(expand('x[a-cX]').values).toEqual(['xX', 'xa', 'xb', 'xc']);
  });

  it('treats a dash at either end of a set as a literal', () => {
    expect(expand('a[_.-]b').values).toEqual(['a-b', 'a.b', 'a_b']);
    expect(expand('a[-_]b').values).toEqual(['a-b', 'a_b']);
  });

  it('supports exact, ranged and alternative lengths', () => {
    expect(expand('c[0-1]{2}').values).toEqual(['c00', 'c01', 'c10', 'c11']);
    expect(expand('j[a-b]{0-1}').values).toEqual(['j', 'ja', 'jb']);
    expect(expand('u[a]{1;3}').values).toEqual(['ua', 'uaaa']);
    expect(expand('u[a]{0-1;3}').values).toEqual(['u', 'ua', 'uaaa']);
  });

  it('combines several blocks and keeps case variants', () => {
    expect(expand('[jJ]ohn[0-1]').values).toEqual(['John0', 'John1', 'john0', 'john1']);
  });

  it('honours escapes for literal brackets and backslash', () => {
    expect(expand('hello\\[w\\]').values).toEqual(['hello[w]']);
    expect(expand('a[\\]b]').values).toEqual(['a]', 'ab']);
  });

  it('reports the full count while returning only the first `limit` values', () => {
    const result = expand('user[0-9]{0-2}', 5);
    expect(result.total).toBe(111);
    expect(result.values).toEqual(['user', 'user0', 'user1', 'user2', 'user3']);
    expect(expand('user[0-9]{0-2}').values).toHaveLength(Math.min(111, MAX_PATTERN_SHOWN));
  });

  it('dedupes expansions that collide', () => {
    expect(expand('a[bb]').values).toEqual(['ab']);
  });

  it('refuses a pattern too broad to be useful without expanding it', () => {
    expect(expandPattern('[a-z]{5}')).toEqual({ ok: false, error: 'tooBroad' });
    expect(expandPattern('[0-9]{4}').ok).toBe(true); // exactly MAX_PATTERN_TOTAL
    expect(MAX_PATTERN_TOTAL).toBe(10_000);
    expect(expandPattern('[a-z]{40}')).toEqual({ ok: false, error: 'tooBroad' });
  });

  it.each([
    ['john[abc', 'missing "]"'],
    ['john[]', 'empty set'],
    ['john[z-a]', 'descending range'],
    ['john[a]{2-1}', 'descending length'],
    ['john[a]{x}', 'bad length'],
    ['john[a]{1', 'missing "}"'],
    ['john]', 'unexpected'],
    ['john\\q', 'bad escape'],
  ])('rejects %s as a syntax error', (pattern, detail) => {
    const result = expandPattern(pattern);
    expect(result.ok).toBe(false);
    expect(result).toMatchObject({ error: 'syntax' });
    expect((result as Rejected).detail).toContain(detail);
  });
});
