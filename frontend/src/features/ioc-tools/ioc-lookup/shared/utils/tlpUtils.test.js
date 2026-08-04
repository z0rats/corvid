import { getOverallTlp } from './tlpUtils';

describe('getOverallTlp', () => {
  it('returns WHITE when given an empty or missing list', () => {
    expect(getOverallTlp([])).toBe('WHITE');
    expect(getOverallTlp(null)).toBe('WHITE');
    expect(getOverallTlp(undefined)).toBe('WHITE');
  });

  it('returns the single TLP value when only one is present', () => {
    expect(getOverallTlp(['GREEN'])).toBe('GREEN');
  });

  it('picks the highest-priority TLP per the RED > AMBER > GREEN > BLUE > WHITE hierarchy', () => {
    expect(getOverallTlp(['GREEN', 'RED', 'BLUE'])).toBe('RED');
    expect(getOverallTlp(['BLUE', 'AMBER'])).toBe('AMBER');
    expect(getOverallTlp(['WHITE', 'BLUE'])).toBe('BLUE');
  });

  it('ignores duplicate and unrecognized values, still finding the highest known one', () => {
    expect(getOverallTlp(['GREEN', 'GREEN', 'UNKNOWN'])).toBe('GREEN');
  });

  it('falls back to WHITE when no recognized TLP values are present', () => {
    expect(getOverallTlp(['UNKNOWN', 'ALSO_UNKNOWN'])).toBe('WHITE');
  });
});
