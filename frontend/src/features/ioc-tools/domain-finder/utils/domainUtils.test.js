import { domainUtils } from './domainUtils';

describe('getStatusColor', () => {
  it('maps 2xx to green, 4xx to orange, 5xx to red', () => {
    expect(domainUtils.getStatusColor(200)).toBe('green');
    expect(domainUtils.getStatusColor('404')).toBe('orange');
    expect(domainUtils.getStatusColor(503)).toBe('red');
  });

  it('falls back to darkgrey for a missing or unrecognized status', () => {
    expect(domainUtils.getStatusColor(null)).toBe('darkgrey');
    expect(domainUtils.getStatusColor(0)).toBe('darkgrey');
    expect(domainUtils.getStatusColor(301)).toBe('darkgrey');
  });
});

describe('formatDate', () => {
  it('returns an empty string for a falsy input', () => {
    expect(domainUtils.formatDate('')).toBe('');
    expect(domainUtils.formatDate(null)).toBe('');
  });

  it('formats a valid date string in de-DE day/month/year + time', () => {
    const formatted = domainUtils.formatDate('2024-01-15T10:30:00Z');
    expect(formatted).toMatch(/^\d{2}\.\d{2}\.2024, \d{2}:\d{2}$/);
  });
});

describe('validateDomainPattern', () => {
  it('accepts a non-blank string', () => {
    expect(domainUtils.validateDomainPattern('example.com')).toBe(true);
  });

  it('rejects blank, non-string, or missing input', () => {
    expect(domainUtils.validateDomainPattern('   ')).toBe(false);
    expect(domainUtils.validateDomainPattern(null)).toBe(false);
    expect(domainUtils.validateDomainPattern(42)).toBe(false);
  });
});

describe('normalizeDomainInput', () => {
  it('returns an empty string for empty or non-string input', () => {
    expect(domainUtils.normalizeDomainInput('')).toBe('');
    expect(domainUtils.normalizeDomainInput(null)).toBe('');
    expect(domainUtils.normalizeDomainInput(undefined)).toBe('');
  });

  it('strips scheme and trailing slash from a full URL', () => {
    expect(domainUtils.normalizeDomainInput('https://nitkatea.com/')).toBe('nitkatea.com');
    expect(domainUtils.normalizeDomainInput('http://example.com')).toBe('example.com');
  });

  it('strips a path after the domain', () => {
    expect(domainUtils.normalizeDomainInput('https://example.com/path/to/page')).toBe('example.com');
  });

  it('strips a port', () => {
    expect(domainUtils.normalizeDomainInput('example.com:8080')).toBe('example.com');
    expect(domainUtils.normalizeDomainInput('https://example.com:8080/')).toBe('example.com');
  });

  it('trims and lowercases a bare domain', () => {
    expect(domainUtils.normalizeDomainInput('  Example.COM  ')).toBe('example.com');
  });

  it('leaves wildcard search patterns untouched', () => {
    expect(domainUtils.normalizeDomainInput('*.example.com')).toBe('*.example.com');
  });
});
