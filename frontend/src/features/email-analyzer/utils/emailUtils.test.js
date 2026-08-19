import { emailUtils } from './emailUtils';

describe('emailUtils.extractEmailAddress', () => {
  it('extracts an email address from surrounding text', () => {
    expect(emailUtils.extractEmailAddress('From: John Doe <john.doe@example.com>')).toBe(
      'john.doe@example.com',
    );
  });

  it('returns the first match when multiple addresses are present', () => {
    expect(emailUtils.extractEmailAddress('a@example.com and b@example.com')).toBe('a@example.com');
  });

  it('returns null when no address is present', () => {
    expect(emailUtils.extractEmailAddress('no address here')).toBeNull();
  });
});

describe('emailUtils.getHashType', () => {
  it.each([
    ['a'.repeat(32), 'MD5'],
    ['a'.repeat(40), 'SHA1'],
    ['a'.repeat(64), 'SHA256'],
    ['a'.repeat(10), 'MD5'],
  ])('classifies a %s-char hash as %s', (hash, expected) => {
    expect(emailUtils.getHashType(hash)).toBe(expected);
  });

  it('defaults to MD5 for a falsy hash', () => {
    expect(emailUtils.getHashType(null)).toBe('MD5');
    expect(emailUtils.getHashType('')).toBe('MD5');
  });
});

describe('emailUtils.formatFileSize', () => {
  it('returns "0 Bytes" for zero', () => {
    expect(emailUtils.formatFileSize(0)).toBe('0 Bytes');
  });

  it.each([
    [500, '500 Bytes'],
    [1024, '1 KB'],
    [1536, '1.5 KB'],
    [1024 * 1024, '1 MB'],
    [1024 * 1024 * 1024, '1 GB'],
  ])('formats %i bytes as %s', (bytes, expected) => {
    expect(emailUtils.formatFileSize(bytes)).toBe(expected);
  });
});

describe('emailUtils.getWarningLevel', () => {
  it.each([
    ['red', 'error'],
    ['orange', 'warning'],
    ['green', 'success'],
    ['white', 'info'],
    [undefined, 'info'],
  ])('maps tlp %s to severity %s', (tlp, expected) => {
    expect(emailUtils.getWarningLevel(tlp)).toBe(expected);
  });
});
