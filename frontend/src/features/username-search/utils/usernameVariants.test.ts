import { generateUsernameVariants, tokenize, MAX_VARIANTS } from './usernameVariants';

const values = (input: string) => generateUsernameVariants(input).map((v) => v.value);

describe('tokenize', () => {
  it('splits separators, camelCase and digit boundaries', () => {
    expect(tokenize('JohnSmith_90')).toEqual(['john', 'smith', '90']);
    expect(tokenize('john.smith-x')).toEqual(['john', 'smith', 'x']);
  });
});

describe('generateUsernameVariants', () => {
  it('returns nothing for empty input and never echoes the original', () => {
    expect(generateUsernameVariants('  ')).toEqual([]);
    expect(values('johnsmith')).not.toContain('johnsmith');
  });

  it('varies separators for multi-token handles', () => {
    expect(values('john.smith')).toEqual(expect.arrayContaining(['johnsmith', 'john_smith', 'john-smith']));
  });

  it('drops and rewrites a trailing year', () => {
    const out = values('john_1990');
    expect(out).toEqual(expect.arrayContaining(['john', 'john90']));
    expect(values('john90')).toContain('john1990');
  });

  it('suggests first/last name patterns for a two-word handle', () => {
    expect(values('john.smith')).toEqual(expect.arrayContaining(['jsmith', 'johns', 'smithjohn']));
  });

  it('suggests nicknames and leetspeak', () => {
    expect(values('johnsmith')).not.toContain('johnysmith');
    expect(values('john_smith')).toContain('johny_smith');
    expect(values('darkness')).toContain('d4rkness');
    expect(values('d4rkn3ss')).toContain('darkness');
  });

  it('uses the local part of a pasted email, minus +tag', () => {
    expect(values('john.smith+news@gmail.com')).toContain('john_smith');
  });

  it('dedupes, keeps only valid handles, and respects the cap', () => {
    const out = values('john.smith');
    expect(new Set(out).size).toBe(out.length);
    expect(out.length).toBeLessThanOrEqual(MAX_VARIANTS);
    expect(out.every((v) => /^[a-z0-9][a-z0-9._-]+[a-z0-9]$/.test(v))).toBe(true);
  });
});
