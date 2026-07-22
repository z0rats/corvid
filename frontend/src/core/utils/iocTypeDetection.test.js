import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { detectIocType, IOC_TYPES } from './iocTypeDetection';

// Shared with the backend's test_ioc_type_detection.py via
// testdata/ioc-type-detection-cases.json at the repo root, so the two implementations
// can't silently diverge.
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturePath = path.resolve(__dirname, '../../../../testdata/ioc-type-detection-cases.json');
const HAPPY_PATH_CASES = JSON.parse(fs.readFileSync(fixturePath, 'utf-8'));

describe('detectIocType — shared fixture cross-check', () => {
  it.each(HAPPY_PATH_CASES.map((c) => [c.value, c.expectedType]))(
    'classifies %j as %s',
    (value, expectedType) => {
      expect(detectIocType(value)).toBe(expectedType);
    },
  );
});

describe('detectIocType — edge cases (mirrors backend edge-case tests)', () => {
  it('URL wins over Domain when a scheme is present', () => {
    expect(detectIocType('https://evil.com/login')).toBe(IOC_TYPES.URL);
    expect(detectIocType('evil.com/login')).toBe(IOC_TYPES.UNKNOWN);
  });

  it('does not misclassify an email as a domain', () => {
    expect(detectIocType('first.last@sub.example.co.uk')).toBe(IOC_TYPES.EMAIL);
  });

  it('does not misclassify a domain as an email', () => {
    expect(detectIocType('sub.example.co.uk')).toBe(IOC_TYPES.DOMAIN);
  });

  it('hash-like length boundaries do not bleed into each other', () => {
    expect(detectIocType('a'.repeat(32))).toBe(IOC_TYPES.MD5);
    expect(detectIocType('a'.repeat(40))).toBe(IOC_TYPES.SHA1);
    expect(detectIocType('a'.repeat(64))).toBe(IOC_TYPES.SHA256);
    expect(detectIocType('a'.repeat(31))).toBe(IOC_TYPES.UNKNOWN);
    expect(detectIocType('a'.repeat(33))).toBe(IOC_TYPES.UNKNOWN);
  });

  it('checks EVM address before generic hex-hash patterns', () => {
    expect(detectIocType(`0x${'a'.repeat(40)}`)).toBe(IOC_TYPES.EVM_ADDRESS);
  });

  it('strips whitespace before classification', () => {
    expect(detectIocType('  8.8.8.8  ')).toBe(IOC_TYPES.IPV4);
  });

  it('does not misclassify an out-of-range IPv4 octet', () => {
    expect(detectIocType('999.999.999.999')).not.toBe(IOC_TYPES.IPV4);
  });
});
