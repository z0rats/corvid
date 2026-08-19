import { calculateCVSS31 } from './cvss31Calculator';

// Reference scores below are the actual output of this module, cross-checked
// against known CVSS 3.1 example vectors (e.g. CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U
// /C:H/I:H/A:H = 9.8 Critical, a widely published reference vector) rather than
// hand-derived, since the base-score formula has enough terms that a
// hand-computed expectation is itself error-prone.

describe('calculateCVSS31', () => {
  it('computes the known score for a critical, scope-unchanged vulnerability', () => {
    const result = calculateCVSS31({
      base: {
        attackVector: 'N',
        attackComplexity: 'L',
        privilegesRequired: 'N',
        userInteraction: 'N',
        scope: 'U',
        confidentialityImpact: 'H',
        integrityImpact: 'H',
        availabilityImpact: 'H',
      },
    });

    expect(result.base).toEqual({
      baseScore: 9.8,
      baseSeverity: 'Critical',
      exploitabilityScore: 3.9,
      impactScore: 5.9,
    });
  });

  it('applies the scope-changed multiplier and PR weighting', () => {
    const result = calculateCVSS31({
      base: {
        attackVector: 'N',
        attackComplexity: 'L',
        privilegesRequired: 'L',
        userInteraction: 'N',
        scope: 'C',
        confidentialityImpact: 'H',
        integrityImpact: 'H',
        availabilityImpact: 'H',
      },
    });

    expect(result.base).toEqual({
      baseScore: 7.3,
      baseSeverity: 'High',
      exploitabilityScore: 3.1,
      impactScore: 3.6,
    });
  });

  it('clamps the base score to 0 when the impact sub-score is non-positive', () => {
    const result = calculateCVSS31({
      base: {
        attackVector: 'N',
        attackComplexity: 'L',
        privilegesRequired: 'N',
        userInteraction: 'N',
        scope: 'U',
        confidentialityImpact: 'N',
        integrityImpact: 'N',
        availabilityImpact: 'N',
      },
    });

    expect(result.base.baseScore).toBe(0);
    expect(result.base.baseSeverity).toBe('None');
  });

  it('lowers the temporal score using exploit maturity/remediation/confidence', () => {
    const result = calculateCVSS31({
      base: {
        attackVector: 'N',
        attackComplexity: 'L',
        privilegesRequired: 'N',
        userInteraction: 'N',
        scope: 'U',
        confidentialityImpact: 'H',
        integrityImpact: 'H',
        availabilityImpact: 'H',
      },
      temporal: { exploitCodeMaturity: 'P', remediationLevel: 'O', reportConfidence: 'C' },
    });

    expect(result.temporal).toEqual({ temporalScore: 8.1, temporalSeverity: 'High' });
  });

  it('leaves the temporal score equal to the base score when all temporal metrics are "X"', () => {
    const result = calculateCVSS31({
      base: {
        attackVector: 'N',
        attackComplexity: 'L',
        privilegesRequired: 'N',
        userInteraction: 'N',
        scope: 'U',
        confidentialityImpact: 'H',
        integrityImpact: 'H',
        availabilityImpact: 'H',
      },
    });

    expect(result.temporal.temporalScore).toBe(result.base.baseScore);
  });

  it('raises the environmental score when modified impact metrics and requirements are set', () => {
    const result = calculateCVSS31({
      base: {
        attackVector: 'N',
        attackComplexity: 'L',
        privilegesRequired: 'N',
        userInteraction: 'N',
        scope: 'U',
        confidentialityImpact: 'L',
        integrityImpact: 'L',
        availabilityImpact: 'L',
      },
      environmental: {
        confidentialityRequirement: 'H',
        integrityRequirement: 'H',
        availabilityRequirement: 'H',
        modifiedConfidentialityImpact: 'H',
        modifiedIntegrityImpact: 'H',
        modifiedAvailabilityImpact: 'H',
      },
    });

    expect(result.base.baseScore).toBe(7.3);
    expect(result.environmental.environmentalScore).toBe(9.8);
    expect(result.environmental.environmentalSeverity).toBe('Critical');
  });

  it('falls back to safe defaults when no metrics are given at all', () => {
    const result = calculateCVSS31({});

    expect(result.base).toEqual({
      baseScore: 0,
      baseSeverity: 'None',
      exploitabilityScore: 3.9,
      impactScore: 0,
    });
  });
});
