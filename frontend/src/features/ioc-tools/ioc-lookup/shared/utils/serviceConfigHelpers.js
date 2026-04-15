/**
 * Wraps a getSummaryAndTlp function with standard error handling.
 * If responseData contains an error, returns an error summary with WHITE TLP.
 */
export const withErrorHandling = (fn) => (responseData) => {
  if (responseData?.error) {
    return {
      summary: `Error: ${responseData.message || responseData.error}`,
      tlp: 'WHITE',
    };
  }
  return fn(responseData);
};

/**
 * Wraps a getSummaryAndTlp function with a no-data check.
 * If responseData (or a nested path within it) is missing or empty, returns a no-data summary.
 */
export const withNoDataCheck = (fn, path) => (responseData) => {
  const target = path ? responseData?.[path] : responseData;
  if (!target) {
    return { summary: 'No data available', tlp: 'WHITE' };
  }
  return fn(responseData);
};

/**
 * Maps a numeric score to a TLP level based on configurable thresholds.
 * Returns 'RED' if score >= red threshold, 'AMBER' if >= amber threshold, else 'GREEN'.
 */
export const scoreTlpMapper = (score, thresholds = { red: 75, amber: 25 }) => {
  if (score >= thresholds.red) return 'RED';
  if (score >= thresholds.amber) return 'AMBER';
  return 'GREEN';
};
