export const exploitabilityMetrics = [
  {
    key: "attackVector",
    label: "Attack Vector (AV)",
    options: [
      { value: "N", label: "Network" },
      { value: "A", label: "Adjacent Network" },
      { value: "L", label: "Local" },
      { value: "P", label: "Physical" },
    ],
    info: "The Attack Vector (AV) metric measures the context by which a vulnerability is exploited. The more remote the attack, the higher the value of AV. The AV metric is based on the assumption that an attacker who can exploit the vulnerability must be able to reach the vulnerable component.",
  },
  {
    key: "attackComplexity",
    label: "Attack Complexity (AC)",
    options: [
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric describes the conditions beyond the attacker's control that must exist in order to exploit the vulnerability. The Base Score is greatest for the least complex attacks.",
  },
  {
    key: "privilegesRequired",
    label: "Privileges Required (PR)",
    options: [
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric describes the level of privileges an attacker must possess before successfully exploiting the vulnerability. The Base Score is greatest if no privileges are required.",
  },
  {
    key: "userInteraction",
    label: "User Interaction (UI)",
    options: [
      { value: "N", label: "None" },
      { value: "R", label: "Required" },
    ],
    info: "This metric captures the requirement for a human user, other than the attacker, to participate in the successful compromise of the vulnerable component. The Base Score is greatest when no user interaction is required.",
  },
];

export const impactMetrics = [
  {
    key: "confidentialityImpact",
    label: "Confidentiality Impact (C)",
    options: [
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to the confidentiality of the information resources managed by a software component due to a successfully exploited vulnerability. The Base Score is greatest when the loss to the impacted component is highest.",
  },
  {
    key: "integrityImpact",
    label: "Integrity Impact (I)",
    options: [
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to integrity of a successfully exploited vulnerability. The Base Score is greatest when the consequence to the impacted component is highest.",
  },
  {
    key: "availabilityImpact",
    label: "Availability Impact (A)",
    options: [
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to the availability of the impacted component resulting from a successfully exploited vulnerability. The Base Score is greatest when the consequence to the impacted component is highest.",
  },
];

export const temporalMetrics = [
  {
    key: "exploitCodeMaturity",
    label: "Exploit Code Maturity (E)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "U", label: "Unproven that exploit exists" },
      { value: "P", label: "Proof of concept code" },
      { value: "F", label: "Functional exploit exists" },
      { value: "H", label: "High" },
    ],
  },
  {
    key: "remediationLevel",
    label: "Remediation Level (RL)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "O", label: "Official fix" },
      { value: "T", label: "Temporary fix" },
      { value: "W", label: "Workaround" },
      { value: "U", label: "Unavailable" },
    ],
  },
  {
    key: "reportConfidence",
    label: "Report Confidence (RC)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "U", label: "Unknown" },
      { value: "R", label: "Reasonable" },
      { value: "C", label: "Confirmed" },
    ],
  },
];

export const environmentalExploitabilityMetrics = [
  {
    key: "modifiedAttackVector",
    label: "Attack Vector (MAV)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "N", label: "Network" },
      { value: "A", label: "Adjacent Network" },
      { value: "L", label: "Local" },
      { value: "P", label: "Physical" },
    ],
  },
  {
    key: "modifiedAttackComplexity",
    label: "Attack Complexity (MAC)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
  },
  {
    key: "modifiedPrivilegesRequired",
    label: "Privileges Required (MPR)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
  },
  {
    key: "modifiedUserInteraction",
    label: "User Interaction (MUI)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "N", label: "None" },
      { value: "R", label: "Required" },
    ],
  },
  {
    key: "modifiedScope",
    label: "Scope (MS)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "U", label: "Unchanged" },
      { value: "C", label: "Changed" },
    ],
  },
];

export const environmentalImpactMetrics = [
  {
    key: "modifiedConfidentialityImpact",
    label: "Confidentiality Impact (MC)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
  },
  {
    key: "modifiedIntegrityImpact",
    label: "Integrity Impact (MI)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
  },
  {
    key: "modifiedAvailabilityImpact",
    label: "Availability Impact (MA)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
  },
];

export const impactSubscoreModifiers = [
  {
    key: "confidentialityRequirement",
    label: "Confidentiality Requirement (CR)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "L", label: "Low" },
      { value: "M", label: "Medium" },
      { value: "H", label: "High" },
    ],
  },
  {
    key: "integrityRequirement",
    label: "Integrity Requirement (IR)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "L", label: "Low" },
      { value: "M", label: "Medium" },
      { value: "H", label: "High" },
    ],
  },
  {
    key: "availabilityRequirement",
    label: "Availability Requirement (AR)",
    options: [
      { value: "X", label: "Not defined" },
      { value: "L", label: "Low" },
      { value: "M", label: "Medium" },
      { value: "H", label: "High" },
    ],
  },
];
