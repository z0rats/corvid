import { isNewerVersion } from './versionCompare';

describe('isNewerVersion', () => {
  it('returns true when latest has a higher patch version', () => {
    expect(isNewerVersion('2.0.3', '2.0.10')).toBe(true);
  });

  it('returns true when latest has a higher minor or major version', () => {
    expect(isNewerVersion('2.0.3', '2.1.0')).toBe(true);
    expect(isNewerVersion('2.0.3', '3.0.0')).toBe(true);
  });

  it('returns false when versions are equal', () => {
    expect(isNewerVersion('2.0.3', '2.0.3')).toBe(false);
  });

  it('returns false when current is newer than latest', () => {
    expect(isNewerVersion('2.1.0', '2.0.3')).toBe(false);
  });

  it('handles differing segment counts', () => {
    expect(isNewerVersion('2.0', '2.0.1')).toBe(true);
    expect(isNewerVersion('2.0.0', '2.0')).toBe(false);
  });

  it('returns false for missing or non-numeric input', () => {
    expect(isNewerVersion('', '2.0.3')).toBe(false);
    expect(isNewerVersion('2.0.3', '')).toBe(false);
    expect(isNewerVersion('2.0.3', 'dev')).toBe(false);
  });
});
