import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { detectIocType, IOC_TYPES, isPhoneNumberTarget, isSteamProfileTarget, isYoutubeVideoUrl } from './iocTypeDetection';

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

describe('isYoutubeVideoUrl', () => {
  const VIDEO_ID = 'dQw4w9WgXcQ';

  it.each([
    `https://www.youtube.com/watch?v=${VIDEO_ID}`,
    `https://youtube.com/watch?v=${VIDEO_ID}`,
    `https://www.youtube.com/watch?v=${VIDEO_ID}&list=PL123`,
    `https://m.youtube.com/watch?v=${VIDEO_ID}`,
    `https://music.youtube.com/watch?v=${VIDEO_ID}`,
    `https://youtu.be/${VIDEO_ID}`,
    `https://youtu.be/${VIDEO_ID}?si=abc123`,
    `https://www.youtube.com/shorts/${VIDEO_ID}`,
    `https://www.youtube.com/embed/${VIDEO_ID}`,
    `https://www.youtube.com/live/${VIDEO_ID}`,
  ])('accepts %s', (url) => {
    expect(isYoutubeVideoUrl(url)).toBe(true);
    // still plain URL for ioc_lookup's own routing/provider selection - see the
    // YOUTUBE_VIDEO_URL comment in iocTypeDetection.ts for why this stays true
    expect(detectIocType(url)).toBe(IOC_TYPES.URL);
  });

  it.each([
    '',
    'not a url',
    'https://example.com/watch?v=dQw4w9WgXcQ',
    'https://youtube.com.evil.com/watch?v=dQw4w9WgXcQ',
    'https://www.youtube.com/',
    'https://www.youtube.com/channel/UC123456789',
  ])('rejects %s', (url) => {
    expect(isYoutubeVideoUrl(url)).toBe(false);
  });
});

describe('isSteamProfileTarget', () => {
  // Robin Walker's public profile: account id 169802 == STEAM_0:0:84901 == [U:1:169802]
  const ID64 = '76561197960435530';

  it.each([
    ID64,
    `  ${ID64}  `,
    '[U:1:169802]',
    'U:1:169802',
    'STEAM_0:0:84901',
    'STEAM_1:0:84901',
    'steam_0:0:84901',
    `https://steamcommunity.com/profiles/${ID64}`,
    `https://steamcommunity.com/profiles/${ID64}/`,
    `http://www.steamcommunity.com/profiles/${ID64}/friends?foo=bar`,
    `steamcommunity.com/profiles/${ID64}`,
    'https://steamcommunity.com/id/robinwalker',
    'https://www.steamcommunity.com/id/robinwalker/games',
  ])('accepts %s', (value) => {
    expect(isSteamProfileTarget(value)).toBe(true);
  });

  it.each([
    '',
    '   ',
    'robinwalker', // a bare vanity name is intentionally not auto-detected - see the JSDoc
    '12345',
    'not a steam id',
    '12345678901234567', // 17 digits but outside the individual-account SteamID64 range
    '[U:1:0]',
    'STEAM_0:0:0',
    'STEAM_9:0:84901',
    `https://evil.example/profiles/${ID64}`,
    `https://steamcommunity.com.evil.example/profiles/${ID64}`,
    'https://steamcommunity.com/',
    'https://steamcommunity.com/groups/valve',
    'https://steamcommunity.com/id/bad!vanity',
  ])('rejects %s', (value) => {
    expect(isSteamProfileTarget(value)).toBe(false);
  });

  it('stays plain URL/unknown in detectIocType, same treatment as YouTube', () => {
    expect(detectIocType(`https://steamcommunity.com/profiles/${ID64}`)).toBe(IOC_TYPES.URL);
    expect(detectIocType(ID64)).toBe(IOC_TYPES.UNKNOWN);
  });
});

describe('isPhoneNumberTarget', () => {
  it.each(['+15551234567', '+442071838750', '+79991234567', '  +15551234567  '])(
    'accepts %s',
    (value) => {
      expect(isPhoneNumberTarget(value)).toBe(true);
    },
  );

  it.each([
    '',
    '   ',
    '15551234567', // missing leading '+'
    '+0551234567', // leading zero after '+'
    '+1555123', // too short
    'not-a-number',
    '+1 555 123 4567', // formatting punctuation not accepted
  ])('rejects %s', (value) => {
    expect(isPhoneNumberTarget(value)).toBe(false);
  });

  it('stays unknown in detectIocType, same treatment as SteamID64', () => {
    expect(detectIocType('+15551234567')).toBe(IOC_TYPES.UNKNOWN);
  });
});
