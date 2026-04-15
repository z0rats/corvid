export const getSeverityColor = (score, chart) => {
  if (score >= 7.0) return chart.high;
  if (score >= 4.0) return chart.medium;
  if (score === 0) return chart.low;
  return chart.low;
};

export const getFillColor = (value, chartPalette) => {
  if (value >= 0 && value <= 3.9) return chartPalette.low;
  if (value >= 4 && value <= 6.9) return chartPalette.medium;
  if (value >= 7 && value <= 10) return chartPalette.high;
};
