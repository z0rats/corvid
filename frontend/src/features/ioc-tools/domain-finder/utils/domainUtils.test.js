import { domainUtils } from './domainUtils';

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
