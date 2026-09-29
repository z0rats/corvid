import { formatEpoch, formatLocation } from './steamFormat';

describe('formatEpoch', () => {
  it('returns null for missing values', () => {
    expect(formatEpoch(null)).toBeNull();
    expect(formatEpoch(0)).toBeNull();
    expect(formatEpoch(undefined)).toBeNull();
  });

  it('formats epoch seconds as a local date', () => {
    expect(formatEpoch(1063324800)).toBe(new Date(1063324800 * 1000).toLocaleDateString());
  });
});

describe('formatLocation', () => {
  it('returns null without a location or any usable part', () => {
    expect(formatLocation(null)).toBeNull();
    expect(formatLocation({})).toBeNull();
  });

  it('joins resolved names from most to least specific', () => {
    expect(
      formatLocation({ city: 'Moscow', state: 'Moscow', country: 'Russia', country_code: 'RU' }),
    ).toBe('Moscow, Moscow, Russia');
  });

  it('falls back to the country code when names did not resolve', () => {
    expect(formatLocation({ country_code: 'RU', state_code: '48', city_id: 41460 })).toBe('RU');
  });
});
