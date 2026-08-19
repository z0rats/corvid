import { buildCvss31ChartData } from './chartDataBuilder';

describe('buildCvss31ChartData', () => {
  const metrics = {
    base: {
      attackVector: 'N',
      attackComplexity: 'H',
      privilegesRequired: 'L',
      userInteraction: 'R',
      confidentialityImpact: 'H',
      integrityImpact: 'L',
      availabilityImpact: 'N',
    },
  };
  const scores = { base: { baseScore: 7.3, baseSeverity: 'High' } };

  it('produces one data point per base metric plus a trailing Base Score point', () => {
    const data = buildCvss31ChartData(metrics, scores);

    expect(data).toHaveLength(8);
    expect(data.map((d) => d.subject)).toEqual([
      'Attack Vector',
      'Attack Complexity',
      'Privileges Required',
      'User Interaction',
      'Confidentiality',
      'Integrity',
      'Availability',
      'Base Score',
    ]);
  });

  it('normalizes each metric score to a 0-10 scale and looks up its display name', () => {
    const data = buildCvss31ChartData(metrics, scores);

    const attackVector = data.find((d) => d.subject === 'Attack Vector');
    expect(attackVector).toMatchObject({ value: 'N', normalizedScore: 8.5, displayValue: 'Network' });

    const attackComplexity = data.find((d) => d.subject === 'Attack Complexity');
    expect(attackComplexity).toMatchObject({ value: 'H', normalizedScore: 4.4, displayValue: 'High' });
  });

  it('formats the trailing Base Score point from the scores object, not the metric map', () => {
    const data = buildCvss31ChartData(metrics, scores);

    const baseScorePoint = data.find((d) => d.subject === 'Base Score');
    expect(baseScorePoint).toEqual({
      subject: 'Base Score',
      value: 7.3,
      normalizedScore: 7.3,
      displayValue: '7.3 (High)',
    });
  });

  it('falls back to each metric default when the base metric is missing', () => {
    const data = buildCvss31ChartData({}, {});

    const attackVector = data.find((d) => d.subject === 'Attack Vector');
    expect(attackVector).toMatchObject({ value: 'N', displayValue: 'Network' });

    const baseScorePoint = data.find((d) => d.subject === 'Base Score');
    expect(baseScorePoint).toEqual({
      subject: 'Base Score',
      value: 0,
      normalizedScore: 0,
      displayValue: '0.0 (None)',
    });
  });
});
