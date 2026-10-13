import { sortByConfidence } from './confidence';

const site = (name: string, confidence?: string) => ({ site_name: name, extra: confidence ? { confidence } : null });

describe('sortByConfidence', () => {
  it('orders confirmed, likely, candidate, conflicting', () => {
    const sorted = sortByConfidence([
      site('a', 'conflicting'), site('b', 'candidate'), site('c', 'confirmed'), site('d', 'likely'),
    ]);
    expect(sorted.map((s) => s.site_name)).toEqual(['c', 'd', 'b', 'a']);
  });

  it('keeps the incoming order for equal or missing ratings, and does not mutate', () => {
    const input = [site('z'), site('y'), site('x', 'likely')];
    expect(sortByConfidence(input).map((s) => s.site_name)).toEqual(['x', 'z', 'y']);
    expect(input.map((s) => s.site_name)).toEqual(['z', 'y', 'x']);
  });
});
