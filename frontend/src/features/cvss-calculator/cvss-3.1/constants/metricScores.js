export const CVSS_31_METRIC_SCORES = {
  attackVector: {
    N: { name: 'Network', score: 0.85 },
    A: { name: 'Adjacent', score: 0.62 },
    L: { name: 'Local', score: 0.55 },
    P: { name: 'Physical', score: 0.2 },
  },
  attackComplexity: {
    L: { name: 'Low', score: 0.77 },
    H: { name: 'High', score: 0.44 },
  },
  privilegesRequired: {
    N: { name: 'None', score: 0.85 },
    L: { name: 'Low', score: 0.62 },
    H: { name: 'High', score: 0.27 },
  },
  userInteraction: {
    N: { name: 'None', score: 0.85 },
    R: { name: 'Required', score: 0.62 },
  },
  scope: {
    U: { name: 'Unchanged', score: 0 },
    C: { name: 'Changed', score: 1 },
  },
  confidentialityImpact: {
    N: { name: 'None', score: 0 },
    L: { name: 'Low', score: 0.22 },
    H: { name: 'High', score: 0.56 },
  },
  integrityImpact: {
    N: { name: 'None', score: 0 },
    L: { name: 'Low', score: 0.22 },
    H: { name: 'High', score: 0.56 },
  },
  availabilityImpact: {
    N: { name: 'None', score: 0 },
    L: { name: 'Low', score: 0.22 },
    H: { name: 'High', score: 0.56 },
  },
};
