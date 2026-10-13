import { inconclusiveSites } from './siteCheck';

describe('inconclusiveSites', () => {
  it('keeps blocked and invalid checks, never a real answer', () => {
    expect(inconclusiveSites({
      GitHub: 'claimed', GitLab: 'available', Twitter: 'unknown', VK: 'illegal',
    })).toEqual(['Twitter', 'VK']);
  });

  it('is empty for a full scan, which stores no verdicts', () => {
    expect(inconclusiveSites(null)).toEqual([]);
    expect(inconclusiveSites(undefined)).toEqual([]);
  });
});
