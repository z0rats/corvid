import { CVSS_31_METRIC_SCORES } from '../constants/metricScores';

const DEFAULT_ENTRY = { name: 'Unknown', score: 0 };

function getMetricEntry(metricKey, value, fallbackValue) {
  const metricMap = CVSS_31_METRIC_SCORES[metricKey];
  if (!metricMap) return DEFAULT_ENTRY;
  return metricMap[value] || metricMap[fallbackValue] || DEFAULT_ENTRY;
}

export function buildCvss31ChartData(metrics, scores) {
  const metricDefinitions = [
    { subject: 'Attack Vector', key: 'attackVector', fallback: 'N' },
    { subject: 'Attack Complexity', key: 'attackComplexity', fallback: 'L' },
    { subject: 'Privileges Required', key: 'privilegesRequired', fallback: 'N' },
    { subject: 'User Interaction', key: 'userInteraction', fallback: 'N' },
    { subject: 'Confidentiality', key: 'confidentialityImpact', fallback: 'N' },
    { subject: 'Integrity', key: 'integrityImpact', fallback: 'N' },
    { subject: 'Availability', key: 'availabilityImpact', fallback: 'N' },
  ];

  const dataPoints = metricDefinitions.map(({ subject, key, fallback }) => {
    const value = metrics.base?.[key] || fallback;
    const entry = getMetricEntry(key, value, fallback);
    return {
      subject,
      value,
      normalizedScore: entry.score * 10,
      displayValue: entry.name,
    };
  });

  dataPoints.push({
    subject: 'Base Score',
    value: scores?.base?.baseScore || 0,
    normalizedScore: scores?.base?.baseScore || 0,
    displayValue: `${(scores?.base?.baseScore || 0).toFixed(1)} (${scores?.base?.baseSeverity || 'None'})`,
  });

  return dataPoints;
}
