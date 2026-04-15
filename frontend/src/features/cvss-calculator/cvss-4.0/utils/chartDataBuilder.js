import { CVSS_40_METRIC_SCORES } from '../constants/metricScores';

const DEFAULT_ENTRY = { name: 'Unknown', score: 0 };

function getMetricEntry(metricKey, value, fallbackValue) {
  const metricMap = CVSS_40_METRIC_SCORES[metricKey];
  if (!metricMap) return DEFAULT_ENTRY;
  return metricMap[value] || metricMap[fallbackValue] || DEFAULT_ENTRY;
}

export function buildCvss40ChartData(metrics, scores) {
  const metricDefinitions = [
    { subject: 'Attack Vector', key: 'attack_vector', fallback: 'N' },
    { subject: 'Attack Complexity', key: 'attack_complexity', fallback: 'L' },
    { subject: 'Attack Requirements', key: 'attack_requirements', fallback: 'N' },
    { subject: 'Privileges Required', key: 'privileges_required', fallback: 'N' },
    { subject: 'User Interaction', key: 'user_interaction', fallback: 'N' },
    { subject: 'V-Confidentiality', key: 'vulnerable_system_confidentiality', fallback: 'N' },
    { subject: 'V-Integrity', key: 'vulnerable_system_integrity', fallback: 'N' },
    { subject: 'V-Availability', key: 'vulnerable_system_availability', fallback: 'N' },
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
    value: scores?.base_score || 0,
    normalizedScore: scores?.base_score || 0,
    displayValue: `${(scores?.base_score || 0).toFixed(1)} (${scores?.base_severity || 'None'})`,
  });

  return dataPoints;
}
