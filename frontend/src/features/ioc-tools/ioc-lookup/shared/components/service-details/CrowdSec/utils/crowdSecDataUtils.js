import { countryCodeMapping } from '../constants/countryCodeMapping';

export function transformDataForPie(data) {
  if (!data) return [];
  return Object.keys(data).map((key) => ({
    id: key,
    label: key,
    value: data[key],
  }));
}

export function transformDataForMap(data) {
  if (!data) return [];
  return Object.keys(data).map((key) => ({
    id: countryCodeMapping[key.toUpperCase()] || key,
    value: data[key],
  }));
}

export function buildScoreData(result) {
  const getScores = (period) => ({
    aggressiveness: result.scores?.[period]?.aggressiveness || 0,
    threat: result.scores?.[period]?.threat || 0,
    trust: result.scores?.[period]?.trust || 0,
    anomaly: result.scores?.[period]?.anomaly || 0,
    total: result.scores?.[period]?.total || 0,
  });

  return [
    { name: "Overall", ...getScores("overall") },
    { name: "Last Day", ...getScores("last_day") },
    { name: "Last Week", ...getScores("last_week") },
    { name: "Last Month", ...getScores("last_month") },
  ];
}
