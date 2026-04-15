import { atom } from 'jotai';
import { selectAtom } from 'jotai/vanilla/utils';
import { calculateCVSS31 } from '../utils/cvss31Calculator';

// CVSS 3.1 State Atom
export const CVSS31_INITIAL = {
  metrics: {
    base: {
      attackVector: "N",
      attackComplexity: "L",
      privilegesRequired: "N",
      userInteraction: "N",
      scope: "U",
      confidentialityImpact: "N",
      integrityImpact: "N",
      availabilityImpact: "N",
    },
    temporal: {
      exploitCodeMaturity: "X",
      remediationLevel: "X",
      reportConfidence: "X",
    },
    environmental: {
      modifiedAttackVector: null,
      modifiedAttackComplexity: null,
      modifiedPrivilegesRequired: null,
      modifiedUserInteraction: null,
      modifiedScope: null,
      modifiedConfidentialityImpact: null,
      modifiedIntegrityImpact: null,
      modifiedAvailabilityImpact: null,
      confidentialityRequirement: "X",
      integrityRequirement: "X",
      availabilityRequirement: "X",
    },
  },
  scores: {
    base: {
      baseScore: 0,
      baseSeverity: "None",
      exploitabilityScore: 0,
      impactScore: 0,
    },
    temporal: {
      temporalScore: 0,
      temporalSeverity: "None",
    },
    environmental: {
      environmentalScore: 0,
      environmentalSeverity: "None",
      modifiedImpactSubScore: 0,
      modifiedImpactScore: 0,
      modifiedExploitabilityScore: 0,
    },
  },
  vectorString: "",
  loading: false,
  error: null,
};

CVSS31_INITIAL.scores = calculateCVSS31(CVSS31_INITIAL.metrics);

export const cvss31Atom = atom(CVSS31_INITIAL);
cvss31Atom.debugLabel = 'cvss31Atom';

// CVSS 3.1 Slice Atoms
const deepEqual = (a, b) => {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (typeof a !== 'object' || typeof b !== 'object') return a === b;
  const keysA = Object.keys(a);
  const keysB = Object.keys(b);
  if (keysA.length !== keysB.length) return false;
  return keysA.every((key) => deepEqual(a[key], b[key]));
};

export const cvss31BaseMetricsAtom = selectAtom(cvss31Atom, (s) => s.metrics.base, deepEqual);
cvss31BaseMetricsAtom.debugLabel = 'cvss31BaseMetricsAtom';
export const cvss31TemporalMetricsAtom = selectAtom(cvss31Atom, (s) => s.metrics.temporal, deepEqual);
cvss31TemporalMetricsAtom.debugLabel = 'cvss31TemporalMetricsAtom';
export const cvss31EnvironmentalMetricsAtom = selectAtom(cvss31Atom, (s) => s.metrics.environmental, deepEqual);
cvss31EnvironmentalMetricsAtom.debugLabel = 'cvss31EnvironmentalMetricsAtom';
export const cvss31ScoresAtom = selectAtom(cvss31Atom, (s) => s.scores, deepEqual);
cvss31ScoresAtom.debugLabel = 'cvss31ScoresAtom';
export const cvss31VectorStringAtom = selectAtom(cvss31Atom, (s) => s.vectorString);
cvss31VectorStringAtom.debugLabel = 'cvss31VectorStringAtom';
export const cvss31ErrorAtom = selectAtom(cvss31Atom, (s) => s.error);
cvss31ErrorAtom.debugLabel = 'cvss31ErrorAtom';
export const cvss31LoadingAtom = selectAtom(cvss31Atom, (s) => s.loading);
cvss31LoadingAtom.debugLabel = 'cvss31LoadingAtom';

// CVSS 4.0 State Atom
export const CVSS40_INITIAL = {
  metrics: {
    base: {
      attack_vector: "N",
      attack_complexity: "L",
      attack_requirements: "N",
      privileges_required: "N",
      user_interaction: "N",
      vulnerable_system_confidentiality: "N",
      vulnerable_system_integrity: "N",
      vulnerable_system_availability: "N",
      subsequent_system_confidentiality: "N",
      subsequent_system_integrity: "N",
      subsequent_system_availability: "N",
    },
    threat: {
      exploit_maturity: "X",
    },
    supplemental: {
      safety: "X",
      automatable: "X",
      recovery: "X",
      value_density: "X",
      vulnerability_response_effort: "X",
      provider_urgency: "X",
    },
    environmental: {
      modified_attack_vector: "X",
      modified_attack_complexity: "X",
      modified_attack_requirements: "X",
      modified_privileges_required: "X",
      modified_user_interaction: "X",
      modified_vulnerable_system_confidentiality: "X",
      modified_vulnerable_system_integrity: "X",
      modified_vulnerable_system_availability: "X",
      modified_subsequent_system_confidentiality: "X",
      modified_subsequent_system_integrity: "X",
      modified_subsequent_system_availability: "X",
    },
  },
  scores: {
    base_score: 0,
    base_severity: "None",
    threat_score: 0,
    threat_severity: "None",
    environmental_score: 0,
    environmental_severity: "None",
  },
  vectorString: "",
  loading: false,
  error: null,
};

export const cvss40Atom = atom(CVSS40_INITIAL);
cvss40Atom.debugLabel = 'cvss40Atom';

// CVSS 4.0 Slice Atoms
export const cvss40BaseMetricsAtom = selectAtom(cvss40Atom, (s) => s.metrics.base, deepEqual);
cvss40BaseMetricsAtom.debugLabel = 'cvss40BaseMetricsAtom';
export const cvss40ThreatMetricsAtom = selectAtom(cvss40Atom, (s) => s.metrics.threat, deepEqual);
cvss40ThreatMetricsAtom.debugLabel = 'cvss40ThreatMetricsAtom';
export const cvss40SupplementalMetricsAtom = selectAtom(cvss40Atom, (s) => s.metrics.supplemental, deepEqual);
cvss40SupplementalMetricsAtom.debugLabel = 'cvss40SupplementalMetricsAtom';
export const cvss40EnvironmentalMetricsAtom = selectAtom(cvss40Atom, (s) => s.metrics.environmental, deepEqual);
cvss40EnvironmentalMetricsAtom.debugLabel = 'cvss40EnvironmentalMetricsAtom';
export const cvss40ScoresAtom = selectAtom(cvss40Atom, (s) => s.scores, deepEqual);
cvss40ScoresAtom.debugLabel = 'cvss40ScoresAtom';
export const cvss40VectorStringAtom = selectAtom(cvss40Atom, (s) => s.vectorString);
cvss40VectorStringAtom.debugLabel = 'cvss40VectorStringAtom';
export const cvss40ErrorAtom = selectAtom(cvss40Atom, (s) => s.error);
cvss40ErrorAtom.debugLabel = 'cvss40ErrorAtom';
export const cvss40LoadingAtom = selectAtom(cvss40Atom, (s) => s.loading);
cvss40LoadingAtom.debugLabel = 'cvss40LoadingAtom';
