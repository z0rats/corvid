import { generateYaraRule, buildConditionString } from './yaraRuleService';

const metadata = { ruleName: 'Suspicious Dropper', author: 'analyst' };
const noStrings = [];
const noConditions = {};
const noTags = [];

describe('generateYaraRule', () => {
  it('replaces spaces in the rule name and opens a brace block', () => {
    const rule = generateYaraRule(metadata, noStrings, noConditions, noTags);
    expect(rule).toMatch(/^rule Suspicious_Dropper \{\n/);
    expect(rule.trim().endsWith('}')).toBe(true);
  });

  it('appends a colon-separated tag list to the rule declaration when tags are given', () => {
    const rule = generateYaraRule(metadata, noStrings, noConditions, [
      { value: 'malware' },
      { value: 'dropper' },
    ]);

    expect(rule).toContain('rule Suspicious_Dropper : malware dropper {');
  });

  it('renders every truthy metadata field under meta:', () => {
    const rule = generateYaraRule(
      { ruleName: 'x', author: 'analyst', description: '', hash: 'abc123' },
      noStrings,
      noConditions,
      noTags,
    );

    expect(rule).toContain('meta:\n');
    expect(rule).toContain('    author = "analyst"\n');
    expect(rule).toContain('    hash = "abc123"\n');
    expect(rule).not.toContain('description =');
  });

  it('omits the strings: section entirely when there are none', () => {
    const rule = generateYaraRule(metadata, noStrings, noConditions, noTags);
    expect(rule).not.toContain('strings:');
  });

  it('renders a text string in double quotes', () => {
    const rule = generateYaraRule(
      metadata,
      [{ identifier: 'a', type: 'text', value: 'evil.exe', modifiers: [] }],
      noConditions,
      noTags,
    );

    expect(rule).toContain('$a = "evil.exe"\n');
  });

  it('renders a hex string in braces', () => {
    const rule = generateYaraRule(
      metadata,
      [{ identifier: 'a', type: 'hex', value: '4D 5A 90', modifiers: [] }],
      noConditions,
      noTags,
    );

    expect(rule).toContain('$a = { 4D 5A 90 }\n');
  });

  it('renders a regex string between slashes', () => {
    const rule = generateYaraRule(
      metadata,
      [{ identifier: 'a', type: 'regex', value: 'foo.*bar', modifiers: [] }],
      noConditions,
      noTags,
    );

    expect(rule).toContain('$a = /foo.*bar/\n');
  });

  it('appends string modifiers after the value', () => {
    const rule = generateYaraRule(
      metadata,
      [{ identifier: 'a', type: 'text', value: 'x', modifiers: ['nocase', 'ascii'] }],
      noConditions,
      noTags,
    );

    expect(rule).toContain('$a = "x" nocase ascii\n');
  });

  it('always includes a condition: section, defaulting to true', () => {
    const rule = generateYaraRule(metadata, noStrings, noConditions, noTags);
    expect(rule).toContain('condition:\n    true\n');
  });
});

describe('buildConditionString', () => {
  it('returns "true" when nothing is set', () => {
    expect(buildConditionString({})).toBe('true');
  });

  it('prefers "all of them" over "any of them" when both flags are set', () => {
    expect(buildConditionString({ all: true, any: true })).toBe('all of them');
  });

  it('uses "any of them" when only the any flag is set', () => {
    expect(buildConditionString({ any: true })).toBe('any of them');
  });

  it('adds a filesize clause', () => {
    expect(buildConditionString({ filesize: '500' })).toBe('filesize < 500KB');
  });

  it('adds a filetype signature clause for a known file type', () => {
    expect(buildConditionString({ filetype: 'pdf' })).toBe('uint16(0) == 0x2550');
  });

  it('ignores an unknown filetype rather than throwing', () => {
    expect(buildConditionString({ filetype: 'not-a-real-type' })).toBe('true');
  });

  it('joins multiple clauses with "and"', () => {
    expect(buildConditionString({ any: true, filesize: '100', filetype: 'exe' })).toBe(
      'any of them and filesize < 100KB and uint16(0) == 0x5A4D',
    );
  });
});
