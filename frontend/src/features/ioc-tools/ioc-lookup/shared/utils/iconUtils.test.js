import { getServiceIcon } from './iconUtils';

describe('getServiceIcon', () => {
  it('returns the icon source for a known icon name', () => {
    expect(getServiceIcon('aipdb_logo_small')).toBeTruthy();
  });

  it('returns the default icon for a missing/empty name', () => {
    expect(getServiceIcon(null)).toBe(getServiceIcon('default_icon'));
    expect(getServiceIcon('')).toBe(getServiceIcon('default_icon'));
    expect(getServiceIcon('default_icon')).toBeTruthy();
  });

  it('falls back to the default icon for an unknown name rather than returning null', () => {
    expect(getServiceIcon('not_a_real_icon')).toBe(getServiceIcon('default_icon'));
  });
});
