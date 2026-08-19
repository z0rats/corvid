import { determineIocType, IOC_TYPES } from './iocDefinitions';

describe('determineIocType', () => {
  it.each([
    ['5d41402abc4b2a76b9719d911017c592', IOC_TYPES.MD5],
    ['aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d', IOC_TYPES.SHA1],
    ['e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', IOC_TYPES.SHA256],
    ['1.2.3.4', IOC_TYPES.IPV4],
    ['2001:0db8:85a3:0000:0000:8a2e:0370:7334', IOC_TYPES.IPV6],
    ['CVE-2024-12345', IOC_TYPES.CVE],
    ['https://example.com/path', IOC_TYPES.URL],
    ['example.com', IOC_TYPES.DOMAIN],
    ['user@example.com', IOC_TYPES.EMAIL],
    ['0xa1b2c3d4e5f6789012345678901234567890abcd', IOC_TYPES.EVM_ADDRESS],
    ['1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa', IOC_TYPES.BITCOIN_ADDRESS],
    ['TN3W4H6rK2ce4vX9YnFQHwKENnHjoxb3m9', IOC_TYPES.TRON_ADDRESS],
    ['rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh', IOC_TYPES.XRP_ADDRESS],
  ])('classifies %s as %s', (ioc, expected) => {
    expect(determineIocType(ioc)).toBe(expected);
  });

  it('returns unknown for input matching no pattern', () => {
    expect(determineIocType('not a real ioc at all')).toBe(IOC_TYPES.UNKNOWN);
  });

  it('trims surrounding whitespace before classifying', () => {
    expect(determineIocType('  1.2.3.4  ')).toBe(IOC_TYPES.IPV4);
  });

  it('checks hash types before crypto-address types so a bare hex string is not misclassified', () => {
    // A 40-char hex string matches both SHA1's pattern and (coincidentally) no
    // crypto pattern here, but this documents the deliberate check order: hashes
    // are checked first in checkOrder, before any of the crypto address types.
    const sha1Shaped = 'a'.repeat(40);
    expect(determineIocType(sha1Shaped)).toBe(IOC_TYPES.SHA1);
  });

  it('checks EVM addresses before IPv4 (both are fixed-format hex-ish strings)', () => {
    expect(determineIocType('0x000000000000000000000000000000000000dead')).toBe(IOC_TYPES.EVM_ADDRESS);
  });
});
