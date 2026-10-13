const SOURCE_LABEL_KEYS = {
  maigret: 'form.sourceMaigret',
  social_analyzer: 'form.sourceSocialAnalyzer',
  threat_actor_usernames: 'form.sourceThreatActorUsernames',
};

export function sourceLabelKey(source) {
  return SOURCE_LABEL_KEYS[source] || SOURCE_LABEL_KEYS.maigret;
}

/** A persisted run's label: a site check is stored as a maigret run, told apart by its verdicts. */
export function runSourceLabelKey(run) {
  return run.site_statuses ? 'form.sourceSiteCheck' : sourceLabelKey(run.source);
}
