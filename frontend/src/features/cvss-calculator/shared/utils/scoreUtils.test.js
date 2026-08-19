import { getSeverityColor, getFillColor } from './scoreUtils';

const chart = { high: 'red', medium: 'orange', low: 'green' };

describe('getSeverityColor', () => {
  it('returns high for scores >= 7.0', () => {
    expect(getSeverityColor(7.0, chart)).toBe('red');
    expect(getSeverityColor(9.8, chart)).toBe('red');
  });

  it('returns medium for scores in [4.0, 7.0)', () => {
    expect(getSeverityColor(4.0, chart)).toBe('orange');
    expect(getSeverityColor(6.9, chart)).toBe('orange');
  });

  it('returns low for a zero score', () => {
    expect(getSeverityColor(0, chart)).toBe('green');
  });

  it('returns low for scores below 4.0 but above zero', () => {
    expect(getSeverityColor(1.5, chart)).toBe('green');
  });
});

describe('getFillColor', () => {
  const palette = { low: '#0f0', medium: '#fa0', high: '#f00' };

  it('returns low for the 0-3.9 band', () => {
    expect(getFillColor(0, palette)).toBe('#0f0');
    expect(getFillColor(3.9, palette)).toBe('#0f0');
  });

  it('returns medium for the 4-6.9 band', () => {
    expect(getFillColor(4, palette)).toBe('#fa0');
    expect(getFillColor(6.9, palette)).toBe('#fa0');
  });

  it('returns high for the 7-10 band', () => {
    expect(getFillColor(7, palette)).toBe('#f00');
    expect(getFillColor(10, palette)).toBe('#f00');
  });

  it('returns undefined outside the defined bands', () => {
    expect(getFillColor(-1, palette)).toBeUndefined();
    expect(getFillColor(10.1, palette)).toBeUndefined();
  });
});
