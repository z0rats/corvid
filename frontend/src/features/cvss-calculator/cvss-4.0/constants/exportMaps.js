export const METRIC_MAPS = {
  attack_vector: { N: "Network", A: "Adjacent", L: "Local", P: "Physical" },
  attack_complexity: { L: "Low", H: "High" },
  attack_requirements: { N: "None", P: "Present" },
  privileges_required: { N: "None", L: "Low", H: "High" },
  user_interaction: { N: "None", P: "Passive", A: "Active" },
  vulnerable_system_confidentiality: { N: "None", L: "Low", H: "High" },
  vulnerable_system_integrity: { N: "None", L: "Low", H: "High" },
  vulnerable_system_availability: { N: "None", L: "Low", H: "High" },
  subsequent_system_confidentiality: { N: "None", L: "Low", H: "High" },
  subsequent_system_integrity: { N: "None", L: "Low", H: "High" },
  subsequent_system_availability: { N: "None", L: "Low", H: "High" },
  exploit_maturity: { X: "Not Defined", U: "Unreported", P: "Proof of Concept", A: "Attacked" },
};
