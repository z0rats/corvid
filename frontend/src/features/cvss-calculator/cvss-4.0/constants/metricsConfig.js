// Base Score - Exploitability Metrics
export const exploitabilityMetrics = [
  {
    key: "attack_vector",
    label: "Attack Vector (AV)",
    options: [
      { value: "N", label: "Network" },
      { value: "A", label: "Adjacent" },
      { value: "L", label: "Local" },
      { value: "P", label: "Physical" },
    ],
    info: "The Attack Vector metric reflects the context by which vulnerability exploitation is possible. This metric value (and consequently the resulting score) will be larger the more remote (logically, and physically) an attacker can be in order to exploit the vulnerable system.",
  },
  {
    key: "attack_complexity",
    label: "Attack Complexity (AC)",
    options: [
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric captures measurable actions that must be taken by the attacker to actively evade or circumvent existing built-in security-enhancing conditions in order to obtain a working exploit.",
  },
  {
    key: "attack_requirements",
    label: "Attack Requirements (AT)",
    options: [
      { value: "N", label: "None" },
      { value: "P", label: "Present" },
    ],
    info: "This metric captures the prerequisite deployment and execution conditions or variables of the vulnerable system that enable the attack.",
  },
  {
    key: "privileges_required",
    label: "Privileges Required (PR)",
    options: [
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric describes the level of privileges an attacker must possess prior to successfully exploiting the vulnerability.",
  },
  {
    key: "user_interaction",
    label: "User Interaction (UI)",
    options: [
      { value: "N", label: "None" },
      { value: "P", label: "Passive" },
      { value: "A", label: "Active" },
    ],
    info: "This metric captures the requirement for a human user, other than the attacker, to participate in the successful compromise of the vulnerable system.",
  },
];

// Base Score - Vulnerable System Impact Metrics
export const vulnerableSystemImpactMetrics = [
  {
    key: "vulnerable_system_confidentiality",
    label: "Confidentiality (VC)",
    options: [
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to the confidentiality of the information managed by the VULNERABLE SYSTEM due to a successfully exploited vulnerability.",
  },
  {
    key: "vulnerable_system_integrity",
    label: "Integrity (VI)",
    options: [
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to integrity of a successfully exploited vulnerability. Integrity refers to the trustworthiness and veracity of information.",
  },
  {
    key: "vulnerable_system_availability",
    label: "Availability (VA)",
    options: [
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to the availability of the VULNERABLE SYSTEM resulting from a successfully exploited vulnerability.",
  },
];

// Base Score - Subsequent System Impact Metrics
export const subsequentSystemImpactMetrics = [
  {
    key: "subsequent_system_confidentiality",
    label: "Confidentiality (SC)",
    options: [
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to the confidentiality of the information managed by the SUBSEQUENT SYSTEM(S) due to a successfully exploited vulnerability.",
  },
  {
    key: "subsequent_system_integrity",
    label: "Integrity (SI)",
    options: [
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to integrity of a successfully exploited vulnerability. Integrity refers to the trustworthiness and veracity of information.",
  },
  {
    key: "subsequent_system_availability",
    label: "Availability (SA)",
    options: [
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to the availability of the SUBSEQUENT SYSTEM(S) resulting from a successfully exploited vulnerability.",
  },
];

// Threat Metrics
export const threatMetrics = [
  {
    key: "exploit_maturity",
    label: "Exploit Maturity (E)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "U", label: "Unreported" },
      { value: "P", label: "Proof of Concept" },
      { value: "A", label: "Attacked" },
    ],
    info: "This metric measures the likelihood of the vulnerability being attacked, and is typically based on the current state of exploit techniques, exploit code availability, or active, 'in-the-wild' exploitation.",
  },
];

// Supplemental Metrics
export const supplementalMetrics = [
  {
    key: "safety",
    label: "Safety (S)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "N", label: "Negligible" },
      { value: "P", label: "Present" },
    ],
    info: "When a system does have an intended use or fitness of purpose aligned to safety, it is possible that exploiting a vulnerability within that system may have Safety impact which can be represented in the Supplemental Metrics group. Lack of a Safety metric being specified does not mean that there may not be any Safety-related impacts.",
  },
  {
    key: "automatable",
    label: "Automatable (AU)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "N", label: "No" },
      { value: "Y", label: "Yes" },
    ],
    info: "The Automatable metric captures the answer to the question 'Can an attacker automate exploitation events for this vulnerability across multiple targets?' based on steps 1-4 of the kill chain.",
  },
  {
    key: "recovery",
    label: "Recovery (R)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "A", label: "Automatic" },
      { value: "U", label: "User" },
      { value: "I", label: "Irrecoverable" },
    ],
    info: "Recovery describes the resilience of a system to recover services, in terms of performance and availability, after an attack has been performed.",
  },
  {
    key: "value_density",
    label: "Value Density (V)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "D", label: "Diffuse" },
      { value: "C", label: "Concentrated" },
    ],
    info: "Value Density describes the resources that the attacker will gain control over with a single exploitation event.",
  },
  {
    key: "vulnerability_response_effort",
    label: "Vulnerability Response Effort (RE)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "L", label: "Low" },
      { value: "M", label: "Moderate" },
      { value: "H", label: "High" },
    ],
    info: "The Vulnerability Response Effort metric reflects the effort required by consumers to respond to a vulnerability within their environment.",
  },
  {
    key: "provider_urgency",
    label: "Provider Urgency (U)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "C", label: "Clear" },
      { value: "G", label: "Green" },
      { value: "A", label: "Amber" },
      { value: "R", label: "Red" },
    ],
    info: "To facilitate a standardized method to incorporate additional provider-supplied assessment, an optional 'pass-through' Supplemental Metric called Provider Urgency is available. Note: While any assessment provider along the product supply chain may provide a Provider Urgency rating, the Penultimate Product Provider (PPP) is best positioned to provide a direct assessment of Provider Urgency.",
  },
];

// Environmental (Modified Base) - Exploitability Metrics
export const modifiedExploitabilityMetrics = [
  {
    key: "modified_attack_vector",
    label: "Attack Vector (MAV)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "N", label: "Network" },
      { value: "A", label: "Adjacent" },
      { value: "L", label: "Local" },
      { value: "P", label: "Physical" },
    ],
    info: "These metrics enable the analyst to override individual Base metrics based on specific characteristics of a user's environment. This metric reflects the context by which vulnerability exploitation is possible in the user's environment.",
  },
  {
    key: "modified_attack_complexity",
    label: "Attack Complexity (MAC)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric captures measurable actions that must be taken by the attacker to actively evade or circumvent existing built-in security-enhancing conditions in the user's environment.",
  },
  {
    key: "modified_attack_requirements",
    label: "Attack Requirements (MAT)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "N", label: "None" },
      { value: "P", label: "Present" },
    ],
    info: "This metric captures the prerequisite deployment and execution conditions or variables of the vulnerable system that enable the attack in the user's environment.",
  },
  {
    key: "modified_privileges_required",
    label: "Privileges Required (MPR)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric describes the level of privileges an attacker must possess prior to successfully exploiting the vulnerability in the user's environment.",
  },
  {
    key: "modified_user_interaction",
    label: "User Interaction (MUI)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "N", label: "None" },
      { value: "P", label: "Passive" },
      { value: "A", label: "Active" },
    ],
    info: "This metric captures the requirement for a human user, other than the attacker, to participate in the successful compromise of the vulnerable system in the user's environment.",
  },
];

// Environmental (Modified Base) - Vulnerable System Impact Metrics
export const modifiedVulnerableSystemImpactMetrics = [
  {
    key: "modified_vulnerable_system_confidentiality",
    label: "Confidentiality (MVC)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to the confidentiality of the information managed by the VULNERABLE SYSTEM due to a successfully exploited vulnerability in the user's environment.",
  },
  {
    key: "modified_vulnerable_system_integrity",
    label: "Integrity (MVI)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to integrity of a successfully exploited vulnerability in the user's environment. Integrity refers to the trustworthiness and veracity of information.",
  },
  {
    key: "modified_vulnerable_system_availability",
    label: "Availability (MVA)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to the availability of the VULNERABLE SYSTEM resulting from a successfully exploited vulnerability in the user's environment.",
  },
];

// Environmental (Modified Base) - Subsequent System Impact Metrics
export const modifiedSubsequentSystemImpactMetrics = [
  {
    key: "modified_subsequent_system_confidentiality",
    label: "Confidentiality (MSC)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to the confidentiality of the information managed by the SUBSEQUENT SYSTEM(S) due to a successfully exploited vulnerability in the user's environment.",
  },
  {
    key: "modified_subsequent_system_integrity",
    label: "Integrity (MSI)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to integrity of a successfully exploited vulnerability in the user's environment. Integrity refers to the trustworthiness and veracity of information.",
  },
  {
    key: "modified_subsequent_system_availability",
    label: "Availability (MSA)",
    options: [
      { value: "X", label: "Not Defined" },
      { value: "N", label: "None" },
      { value: "L", label: "Low" },
      { value: "H", label: "High" },
    ],
    info: "This metric measures the impact to the availability of the SUBSEQUENT SYSTEM(S) resulting from a successfully exploited vulnerability in the user's environment.",
  },
];
