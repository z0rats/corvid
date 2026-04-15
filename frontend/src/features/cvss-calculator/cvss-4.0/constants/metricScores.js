export const CVSS_40_METRIC_SCORES = {
  attack_vector: {
    N: { name: 'Network', score: 0.85 },
    A: { name: 'Adjacent', score: 0.62 },
    L: { name: 'Local', score: 0.55 },
    P: { name: 'Physical', score: 0.2 },
  },
  attack_complexity: {
    L: { name: 'Low', score: 0.77 },
    H: { name: 'High', score: 0.44 },
  },
  attack_requirements: {
    N: { name: 'None', score: 0.85 },
    P: { name: 'Present', score: 0.62 },
  },
  privileges_required: {
    N: { name: 'None', score: 0.85 },
    L: { name: 'Low', score: 0.62 },
    H: { name: 'High', score: 0.27 },
  },
  user_interaction: {
    N: { name: 'None', score: 0.85 },
    P: { name: 'Passive', score: 0.62 },
    A: { name: 'Active', score: 0.45 },
  },
  vulnerable_system_confidentiality: {
    N: { name: 'None', score: 0 },
    L: { name: 'Low', score: 0.22 },
    H: { name: 'High', score: 0.56 },
  },
  vulnerable_system_integrity: {
    N: { name: 'None', score: 0 },
    L: { name: 'Low', score: 0.22 },
    H: { name: 'High', score: 0.56 },
  },
  vulnerable_system_availability: {
    N: { name: 'None', score: 0 },
    L: { name: 'Low', score: 0.22 },
    H: { name: 'High', score: 0.56 },
  },
};
