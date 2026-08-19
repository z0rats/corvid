import { buildCvss40ChartData } from './chartDataBuilder';

describe('buildCvss40ChartData', () => {
  const metrics = {
    base: {
      attack_vector: 'N',
      attack_complexity: 'H',
      attack_requirements: 'P',
      privileges_required: 'L',
      user_interaction: 'A',
      vulnerable_system_confidentiality: 'H',
      vulnerable_system_integrity: 'L',
      vulnerable_system_availability: 'N',
    },
  };
  const scores = { base_score: 6.4, base_severity: 'Medium' };

  it('produces one data point per base metric plus a trailing Base Score point', () => {
    const data = buildCvss40ChartData(metrics, scores);

    expect(data).toHaveLength(9);
    expect(data.map((d) => d.subject)).toEqual([
      'Attack Vector',
      'Attack Complexity',
      'Attack Requirements',
      'Privileges Required',
      'User Interaction',
      'V-Confidentiality',
      'V-Integrity',
      'V-Availability',
      'Base Score',
    ]);
  });

  it('normalizes each metric score to a 0-10 scale and looks up its display name', () => {
    const data = buildCvss40ChartData(metrics, scores);

    const attackRequirements = data.find((d) => d.subject === 'Attack Requirements');
    expect(attackRequirements).toMatchObject({
      value: 'P',
      normalizedScore: 6.2,
      displayValue: 'Present',
    });

    const userInteraction = data.find((d) => d.subject === 'User Interaction');
    expect(userInteraction).toMatchObject({ value: 'A', normalizedScore: 4.5, displayValue: 'Active' });
  });

  it('formats the trailing Base Score point from the scores object', () => {
    const data = buildCvss40ChartData(metrics, scores);

    const baseScorePoint = data.find((d) => d.subject === 'Base Score');
    expect(baseScorePoint).toEqual({
      subject: 'Base Score',
      value: 6.4,
      normalizedScore: 6.4,
      displayValue: '6.4 (Medium)',
    });
  });

  it('falls back to each metric default when the base metric is missing', () => {
    const data = buildCvss40ChartData({}, {});

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
