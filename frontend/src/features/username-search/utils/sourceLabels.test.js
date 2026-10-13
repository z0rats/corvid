import { runSourceLabelKey, sourceLabelKey } from './sourceLabels';

describe('sourceLabelKey', () => {
  it('maps each known source to its i18n key', () => {
    expect(sourceLabelKey('maigret')).toBe('form.sourceMaigret');
    expect(sourceLabelKey('social_analyzer')).toBe('form.sourceSocialAnalyzer');
    expect(sourceLabelKey('threat_actor_usernames')).toBe('form.sourceThreatActorUsernames');
  });

  it('falls back to the maigret key for an unknown source', () => {
    expect(sourceLabelKey('not_a_real_source')).toBe('form.sourceMaigret');
    expect(sourceLabelKey(undefined)).toBe('form.sourceMaigret');
  });
});

describe('runSourceLabelKey', () => {
  it('labels a site check apart from a full maigret scan', () => {
    expect(runSourceLabelKey({ source: 'maigret', site_statuses: { GitHub: 'claimed' } })).toBe('form.sourceSiteCheck');
    expect(runSourceLabelKey({ source: 'maigret', site_statuses: null })).toBe('form.sourceMaigret');
  });
});
