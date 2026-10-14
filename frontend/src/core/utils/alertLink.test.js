import { getAlertLink } from './alertLink';

describe('getAlertLink', () => {
  it('deep-links a scan alert to its run', () => {
    expect(getAlertLink({ module: 'git_recon', message: 'Scan #42 (target=x) completed.' }))
      .toBe('/git-recon/history/42');
  });

  it('routes every username-search source to the username-search history', () => {
    for (const module of ['username_search', 'social_analyzer', 'threat_actor_usernames']) {
      expect(getAlertLink({ module, message: 'Scan #7 (username=a) failed: boom' }))
        .toBe('/username-search/history/7');
    }
  });

  it('falls back to the history list when the message has no run id', () => {
    expect(getAlertLink({ module: 'amass', message: 'something else' })).toBe('/amass/history');
  });

  it('maps non-scan modules to their settings pages', () => {
    expect(getAlertLink({ module: 'api_keys', message: '' })).toBe('/settings/apikeys');
    expect(getAlertLink({ module: 'backup', message: '' })).toBe('/settings/backup');
    expect(getAlertLink({ module: 'newsfeed', message: '' })).toBe('/newsfeed');
  });

  it('returns null for modules with nowhere to go', () => {
    expect(getAlertLink({ module: 'scheduler', message: 'news_fetch: job failing' })).toBeNull();
  });
});
