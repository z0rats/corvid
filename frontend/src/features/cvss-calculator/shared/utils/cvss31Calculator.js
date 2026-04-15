/**
 * Client-side CVSS 3.1 calculator for instant score updates
 * Based on CVSS 3.1 specification
 */

const CVSS31_METRICS = {
  attackVector: {
    'N': 0.85,
    'A': 0.62,
    'L': 0.55,
    'P': 0.2
  },
  attackComplexity: {
    'L': 0.77,
    'H': 0.44
  },
  privilegesRequired: {
    'N': { unchanged: 0.85, changed: 0.85 },
    'L': { unchanged: 0.62, changed: 0.68 },
    'H': { unchanged: 0.27, changed: 0.50 }
  },
  userInteraction: {
    'N': 0.85,
    'R': 0.62
  },
  confidentialityImpact: {
    'N': 0,
    'L': 0.22,
    'H': 0.56
  },
  integrityImpact: {
    'N': 0,
    'L': 0.22,
    'H': 0.56
  },
  availabilityImpact: {
    'N': 0,
    'L': 0.22,
    'H': 0.56
  },
  exploitCodeMaturity: {
    'X': 1.0,
    'U': 0.91,
    'P': 0.94,
    'F': 0.97,
    'H': 1.0
  },
  remediationLevel: {
    'X': 1.0,
    'O': 0.87,
    'T': 0.90,
    'W': 0.95,
    'U': 1.0
  },
  reportConfidence: {
    'X': 1.0,
    'U': 0.92,
    'R': 0.96,
    'C': 1.0
  }
};

const getSeverityRating = (score) => {
  if (score === 0) return 'None';
  if (score >= 0.1 && score <= 3.9) return 'Low';
  if (score >= 4.0 && score <= 6.9) return 'Medium';
  if (score >= 7.0 && score <= 8.9) return 'High';
  if (score >= 9.0 && score <= 10.0) return 'Critical';
  return 'None';
};

const roundUp = (value) => {
  return Math.ceil(value * 10) / 10;
};

export const calculateCVSS31 = (metrics) => {
  const {
    attackVector = 'N',
    attackComplexity = 'L',
    privilegesRequired = 'N',
    userInteraction = 'N',
    scope = 'U',
    confidentialityImpact = 'N',
    integrityImpact = 'N',
    availabilityImpact = 'N'
  } = metrics.base || {};

  const {
    exploitCodeMaturity = 'X',
    remediationLevel = 'X',
    reportConfidence = 'X'
  } = metrics.temporal || {};

  const {
    confidentialityRequirement = 'X',
    integrityRequirement = 'X',
    availabilityRequirement = 'X',
    modifiedAttackVector = null,
    modifiedAttackComplexity = null,
    modifiedPrivilegesRequired = null,
    modifiedUserInteraction = null,
    modifiedScope = null,
    modifiedConfidentialityImpact = null,
    modifiedIntegrityImpact = null,
    modifiedAvailabilityImpact = null
  } = metrics.environmental || {};

  // Base Score Calculation
  const av = CVSS31_METRICS.attackVector[attackVector];
  const ac = CVSS31_METRICS.attackComplexity[attackComplexity];
  const pr = CVSS31_METRICS.privilegesRequired[privilegesRequired][scope === 'C' ? 'changed' : 'unchanged'];
  const ui = CVSS31_METRICS.userInteraction[userInteraction];
  const c = CVSS31_METRICS.confidentialityImpact[confidentialityImpact];
  const i = CVSS31_METRICS.integrityImpact[integrityImpact];
  const a = CVSS31_METRICS.availabilityImpact[availabilityImpact];

  const exploitabilityScore = 8.22 * av * ac * pr * ui;
  const impactScore = scope === 'U' 
    ? 6.42 * (1 - (1 - c) * (1 - i) * (1 - a))
    : 7.52 * (1 - (1 - c) * (1 - i) * (1 - a)) - 0.029 - 3.25 * Math.pow(1 - (1 - c) * (1 - i) * (1 - a), 0.02);

  let baseScore = 0;
  if (impactScore <= 0) {
    baseScore = 0;
  } else if (scope === 'U') {
    baseScore = Math.min(exploitabilityScore + impactScore, 10);
  } else {
    baseScore = Math.min(1.08 * (exploitabilityScore + impactScore), 10);
  }

  baseScore = roundUp(baseScore);
  const baseSeverity = getSeverityRating(baseScore);

  // Temporal Score Calculation
  const e = CVSS31_METRICS.exploitCodeMaturity[exploitCodeMaturity];
  const rl = CVSS31_METRICS.remediationLevel[remediationLevel];
  const rc = CVSS31_METRICS.reportConfidence[reportConfidence];

  const temporalScore = roundUp(baseScore * e * rl * rc);
  const temporalSeverity = getSeverityRating(temporalScore);

  // Environmental Score Calculation (simplified - using base metrics if modified not set)
  const mav = (modifiedAttackVector !== null && modifiedAttackVector !== 'X') ? CVSS31_METRICS.attackVector[modifiedAttackVector] : av;
  const mac = (modifiedAttackComplexity !== null && modifiedAttackComplexity !== 'X') ? CVSS31_METRICS.attackComplexity[modifiedAttackComplexity] : ac;
  const mpr = (modifiedPrivilegesRequired !== null && modifiedPrivilegesRequired !== 'X') 
    ? CVSS31_METRICS.privilegesRequired[modifiedPrivilegesRequired][(modifiedScope !== null && modifiedScope !== 'X') ? (modifiedScope === 'C' ? 'changed' : 'unchanged') : (scope === 'C' ? 'changed' : 'unchanged')]
    : pr;
  const mui = (modifiedUserInteraction !== null && modifiedUserInteraction !== 'X') ? CVSS31_METRICS.userInteraction[modifiedUserInteraction] : ui;
  const mc = (modifiedConfidentialityImpact !== null && modifiedConfidentialityImpact !== 'X') ? CVSS31_METRICS.confidentialityImpact[modifiedConfidentialityImpact] : c;
  const mi = (modifiedIntegrityImpact !== null && modifiedIntegrityImpact !== 'X') ? CVSS31_METRICS.integrityImpact[modifiedIntegrityImpact] : i;
  const ma = (modifiedAvailabilityImpact !== null && modifiedAvailabilityImpact !== 'X') ? CVSS31_METRICS.availabilityImpact[modifiedAvailabilityImpact] : a;

  const cr = confidentialityRequirement !== 'X' ? (confidentialityRequirement === 'H' ? 1.5 : confidentialityRequirement === 'M' ? 1.0 : 0.5) : 1.0;
  const ir = integrityRequirement !== 'X' ? (integrityRequirement === 'H' ? 1.5 : integrityRequirement === 'M' ? 1.0 : 0.5) : 1.0;
  const ar = availabilityRequirement !== 'X' ? (availabilityRequirement === 'H' ? 1.5 : availabilityRequirement === 'M' ? 1.0 : 0.5) : 1.0;

  const modifiedExploitabilityScore = 8.22 * mav * mac * mpr * mui;
  const modifiedImpactSubScore = Math.min(1 - (1 - mc * cr) * (1 - mi * ir) * (1 - ma * ar), 0.915);
  
  const effectiveModifiedScope = (modifiedScope !== null && modifiedScope !== 'X') ? modifiedScope : scope;
  const modifiedImpactScore = effectiveModifiedScope === 'U' 
    ? 6.42 * modifiedImpactSubScore
    : 7.52 * modifiedImpactSubScore - 0.029 - 3.25 * Math.pow(modifiedImpactSubScore, 0.02);

  let environmentalScore = 0;
  if (modifiedImpactScore <= 0) {
    environmentalScore = 0;
  } else if (effectiveModifiedScope === 'U') {
    environmentalScore = Math.min(modifiedExploitabilityScore + modifiedImpactScore, 10);
  } else {
    environmentalScore = Math.min(1.08 * (modifiedExploitabilityScore + modifiedImpactScore), 10);
  }

  environmentalScore = roundUp(environmentalScore * e * rl * rc);
  const environmentalSeverity = getSeverityRating(environmentalScore);

  return {
    base: {
      baseScore,
      baseSeverity,
      exploitabilityScore: Math.round(exploitabilityScore * 10) / 10,
      impactScore: Math.round(impactScore * 10) / 10
    },
    temporal: {
      temporalScore,
      temporalSeverity
    },
    environmental: {
      environmentalScore,
      environmentalSeverity,
      modifiedImpactSubScore: Math.round(modifiedImpactSubScore * 10) / 10,
      modifiedImpactScore: Math.round(modifiedImpactScore * 10) / 10,
      modifiedExploitabilityScore: Math.round(modifiedExploitabilityScore * 10) / 10
    }
  };
};
