import { sourceLabelKey } from './sourceLabels';

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
