import { validators, validateBulkInput } from './validation';

describe('validators.email', () => {
  it('accepts a well-formed email', () => {
    expect(validators.email('a@example.com')).toBe(true);
  });

  it('rejects a string with no @', () => {
    expect(validators.email('not-an-email')).toBe(false);
  });
});

describe('validators.ip', () => {
  it('accepts a valid IPv4 address', () => {
    expect(validators.ip('1.2.3.4')).toBe(true);
  });

  it('accepts a valid IPv6 address', () => {
    expect(validators.ip('2001:0db8:85a3:0000:0000:8a2e:0370:7334')).toBe(true);
  });

  it('rejects an out-of-range IPv4 octet', () => {
    expect(validators.ip('999.1.1.1')).toBe(false);
  });
});

describe('validators.domain', () => {
  it('accepts a well-formed domain', () => {
    expect(validators.domain('example.com')).toBe(true);
  });

  it('rejects a domain longer than 253 characters', () => {
    const longDomain = `${'a'.repeat(250)}.com`;
    expect(validators.domain(longDomain)).toBe(false);
  });

  it('rejects a domain with invalid characters', () => {
    expect(validators.domain('exa mple.com')).toBe(false);
  });
});

describe('validators.url', () => {
  it('accepts a well-formed URL', () => {
    expect(validators.url('https://example.com/path')).toBe(true);
  });

  it('rejects a non-URL string', () => {
    expect(validators.url('not a url')).toBe(false);
  });
});

describe('validators.hash', () => {
  it('accepts an md5 hash', () => {
    expect(validators.hash('d41d8cd98f00b204e9800998ecf8427e')).toBe(true);
  });

  it('accepts a sha256 hash', () => {
    expect(validators.hash('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')).toBe(
      true,
    );
  });

  it('rejects a string of the wrong length', () => {
    expect(validators.hash('abc123')).toBe(false);
  });
});

describe('validators.ioc', () => {
  it('accepts a normal non-empty string', () => {
    expect(validators.ioc('1.2.3.4')).toBe(true);
  });

  it('rejects null, non-strings, and blank input', () => {
    expect(validators.ioc(null)).toBe(false);
    expect(validators.ioc(42)).toBe(false);
    expect(validators.ioc('   ')).toBe(false);
  });

  it('rejects input over 1000 characters', () => {
    expect(validators.ioc('a'.repeat(1001))).toBe(false);
  });
});

describe('validators.sanitizeHtml', () => {
  it('escapes angle brackets and quotes', () => {
    expect(validators.sanitizeHtml(`<a href="x">'y'</a>`)).toBe(
      '&lt;a href=&quot;x&quot;&gt;&#x27;y&#x27;&lt;&#x2F;a&gt;',
    );
  });

  it('returns non-string input unchanged', () => {
    expect(validators.sanitizeHtml(42)).toBe(42);
  });
});

describe('validators.sanitizeInput', () => {
  it('trims whitespace and strips control characters', () => {
    expect(validators.sanitizeInput('  hello\x00world  ')).toBe('helloworld');
  });

  it('truncates to 1000 characters', () => {
    expect(validators.sanitizeInput('a'.repeat(1500))).toHaveLength(1000);
  });

  it('returns non-string input unchanged', () => {
    expect(validators.sanitizeInput(null)).toBeNull();
  });
});

describe('validateBulkInput', () => {
  it('accepts multi-line input and returns the non-blank lines', () => {
    const result = validateBulkInput('1.2.3.4\nexample.com\n\n');
    expect(result).toEqual({ isValid: true, lines: ['1.2.3.4', 'example.com'] });
  });

  it('rejects a non-string input', () => {
    expect(validateBulkInput(null)).toEqual({ isValid: false, error: 'Input must be a string' });
  });

  it('rejects input with no non-blank lines', () => {
    expect(validateBulkInput('   \n  ')).toEqual({ isValid: false, error: 'No valid IOCs found' });
  });

  it('rejects more than 1000 lines', () => {
    const tooMany = Array.from({ length: 1001 }, (_, i) => `ioc-${i}`).join('\n');
    expect(validateBulkInput(tooMany)).toEqual({
      isValid: false,
      error: 'Too many IOCs (maximum 1000)',
    });
  });
});
