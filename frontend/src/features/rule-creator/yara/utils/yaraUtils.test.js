import {
  validateStringIdentifier,
  validateStringValue,
  validateRuleName,
  formatStringForDisplay,
  sanitizeInput,
} from './yaraUtils';

describe('validateStringIdentifier', () => {
  it('accepts a well-formed, unique identifier', () => {
    expect(validateStringIdentifier('my_string1', [])).toEqual({ isValid: true, error: null });
  });

  it('rejects an empty identifier', () => {
    expect(validateStringIdentifier('   ', []).isValid).toBe(false);
  });

  it('rejects an identifier starting with a digit', () => {
    const result = validateStringIdentifier('1abc', []);
    expect(result.isValid).toBe(false);
    expect(result.error).toMatch(/must start with a letter/);
  });

  it('rejects a duplicate identifier', () => {
    const result = validateStringIdentifier('a', [{ identifier: 'a' }]);
    expect(result.isValid).toBe(false);
    expect(result.error).toBe('Identifier must be unique');
  });
});

describe('validateStringValue', () => {
  it('rejects an empty value regardless of type', () => {
    expect(validateStringValue('  ', 'text').isValid).toBe(false);
  });

  it('accepts valid hex digits and spaces', () => {
    expect(validateStringValue('4D 5A 90', 'hex')).toEqual({ isValid: true, error: null });
  });

  it('rejects non-hex characters for a hex string', () => {
    expect(validateStringValue('not hex!', 'hex').isValid).toBe(false);
  });

  it('accepts a well-formed regex', () => {
    expect(validateStringValue('foo.*bar', 'regex')).toEqual({ isValid: true, error: null });
  });

  it('rejects an invalid regex', () => {
    const result = validateStringValue('foo(bar', 'regex');
    expect(result.isValid).toBe(false);
    expect(result.error).toBe('Invalid regular expression');
  });

  it('accepts any non-empty text value', () => {
    expect(validateStringValue('anything', 'text')).toEqual({ isValid: true, error: null });
  });
});

describe('validateRuleName', () => {
  it('accepts a name with spaces (later normalized to underscores)', () => {
    expect(validateRuleName('My Rule')).toEqual({ isValid: true, error: null });
  });

  it('rejects an empty name', () => {
    expect(validateRuleName('   ').isValid).toBe(false);
  });

  it('rejects a name starting with a digit', () => {
    expect(validateRuleName('1_rule').isValid).toBe(false);
  });

  it('rejects a name containing symbols other than spaces/underscores', () => {
    expect(validateRuleName('rule-name!').isValid).toBe(false);
  });
});

describe('formatStringForDisplay', () => {
  it('formats a string without modifiers', () => {
    const result = formatStringForDisplay({
      identifier: 'a',
      type: 'text',
      value: 'evil.exe',
      modifiers: [],
    });
    expect(result).toBe('$a (TEXT): evil.exe');
  });

  it('appends a modifiers suffix when present', () => {
    const result = formatStringForDisplay({
      identifier: 'a',
      type: 'hex',
      value: '4D 5A',
      modifiers: ['nocase', 'wide'],
    });
    expect(result).toBe('$a (HEX) | Modifiers: nocase, wide: 4D 5A');
  });
});

describe('sanitizeInput', () => {
  it('strips angle brackets', () => {
    expect(sanitizeInput('<script>alert(1)</script>')).toBe('scriptalert(1)/script');
  });

  it('leaves normal text untouched', () => {
    expect(sanitizeInput('normal text 123')).toBe('normal text 123');
  });

  it('returns an empty string for a non-string input', () => {
    expect(sanitizeInput(null)).toBe('');
    expect(sanitizeInput(42)).toBe('');
  });
});
