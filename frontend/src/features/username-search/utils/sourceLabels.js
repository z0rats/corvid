const SOURCE_LABEL_KEYS = {
  maigret: 'form.sourceMaigret',
  social_analyzer: 'form.sourceSocialAnalyzer',
  threat_actor_usernames: 'form.sourceThreatActorUsernames',
};

export function sourceLabelKey(source) {
  return SOURCE_LABEL_KEYS[source] || SOURCE_LABEL_KEYS.maigret;
}
