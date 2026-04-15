import { generateSID, getCurrentDate, exportAsFile, validateRequiredFields } from '../../shared/utils/ruleUtils';

/**
 * Generate a complete Snort rule string
 * @param {Object} ruleHeader - Rule header configuration
 * @param {Object} ruleOptions - Rule options
 * @param {Object} ruleContent - Rule content
 * @param {Object} ruleMetadata - Rule metadata
 * @returns {string} Generated Snort rule
 */
export const generateSnortRule = (ruleHeader, ruleOptions, ruleContent, ruleMetadata) => {
  const validationErrors = validateRequiredFields(ruleOptions, ['msg', 'sid']);
  if (validationErrors.length > 0) {
    throw new Error(validationErrors.join(', '));
  }

  // Build rule header
  let rule = `${ruleHeader.action} ${ruleHeader.protocol} ${ruleHeader.sourceIP} ${ruleHeader.sourcePort} ${ruleHeader.direction} ${ruleHeader.destIP} ${ruleHeader.destPort} (`;

  // Build rule options
  const options = [];
  
  // Required options
  options.push(`msg:"${ruleOptions.msg}"`);
  options.push(`sid:${ruleOptions.sid}`);
  options.push(`rev:${ruleOptions.rev}`);

  // Optional basic options
  if (ruleOptions.classtype) options.push(`classtype:${ruleOptions.classtype}`);
  if (ruleOptions.priority) options.push(`priority:${ruleOptions.priority}`);

  // Content options
  ruleContent.content.forEach(content => {
    let contentStr = `content:"${content.value}"`;
    if (content.modifiers && content.modifiers.length > 0) {
      contentStr += `; ${content.modifiers.join('; ')}`;
    }
    options.push(contentStr);
  });

  // PCRE options
  ruleContent.pcre.forEach(pcre => {
    options.push(`pcre:"${pcre.pattern}"`);
  });

  // Flowbits options
  ruleContent.flowbits.forEach(flowbit => {
    options.push(`flowbits:${flowbit.action},${flowbit.name}`);
  });

  // Threshold and detection filter
  if (ruleContent.threshold) options.push(`threshold:${ruleContent.threshold}`);
  if (ruleContent.detection_filter) options.push(`detection_filter:${ruleContent.detection_filter}`);

  // References
  ruleOptions.reference.forEach(ref => {
    options.push(`reference:${ref.type},${ref.value}`);
  });

  // Metadata
  const allMetadata = buildMetadata(ruleOptions.metadata, ruleMetadata);
  if (allMetadata.length > 0) {
    options.push(`metadata:${allMetadata.join(', ')}`);
  }

  rule += options.join('; ');
  rule += ')';

  return rule;
};

/**
 * Build metadata array from basic and enhanced metadata
 * @param {Array} basicMetadata - Basic metadata array
 * @param {Object} enhancedMetadata - Enhanced metadata object
 * @returns {Array} Combined metadata array
 */
export const buildMetadata = (basicMetadata, enhancedMetadata) => {
  const metadata = [];
  
  // Basic metadata
  basicMetadata.forEach(meta => {
    metadata.push(`${meta.key} ${meta.value}`);
  });

  // Enhanced metadata
  if (enhancedMetadata.created_at) metadata.push(`created_at ${enhancedMetadata.created_at}`);
  if (enhancedMetadata.updated_at) metadata.push(`updated_at ${enhancedMetadata.updated_at}`);
  if (enhancedMetadata.policy) metadata.push(`policy ${enhancedMetadata.policy}`);
  if (enhancedMetadata.former_category) metadata.push(`former_category ${enhancedMetadata.former_category}`);
  if (enhancedMetadata.signature_severity) metadata.push(`signature_severity ${enhancedMetadata.signature_severity}`);
  
  enhancedMetadata.attack_target?.forEach(target => metadata.push(`attack_target ${target}`));
  enhancedMetadata.deployment?.forEach(deploy => metadata.push(`deployment ${deploy}`));
  enhancedMetadata.tag?.forEach(tag => metadata.push(`tag ${tag.value}`));
  enhancedMetadata.malware_family?.forEach(family => metadata.push(`malware_family ${family.value}`));

  return metadata;
};

/**
 * Export Snort rule as .rules file
 * @param {string} rule - Generated rule content
 * @param {string} sid - Rule SID for filename
 */
export const exportSnortRule = (rule, sid) => {
  const filename = `snort_rule_${sid}.rules`;
  exportAsFile(rule, filename);
};

/**
 * Create initial rule header configuration
 * @returns {Object} Initial rule header object
 */
export const createInitialRuleHeader = () => ({
  action: 'alert',
  protocol: 'tcp',
  sourceIP: 'any',
  sourcePort: 'any',
  direction: '->',
  destIP: 'any',
  destPort: 'any',
});

/**
 * Create initial rule options configuration
 * @returns {Object} Initial rule options object
 */
export const createInitialRuleOptions = () => ({
  msg: '',
  sid: generateSID().toString(),
  rev: '1',
  classtype: '',
  priority: '3',
  reference: [],
  metadata: [],
});

/**
 * Create initial rule content configuration
 * @returns {Object} Initial rule content object
 */
export const createInitialRuleContent = () => ({
  content: [],
  pcre: [],
  flowbits: [],
  threshold: '',
  detection_filter: '',
});

/**
 * Create initial rule metadata configuration
 * @returns {Object} Initial rule metadata object
 */
export const createInitialRuleMetadata = () => {
  const currentDate = getCurrentDate();
  return {
    created_at: currentDate,
    updated_at: currentDate,
    policy: '',
    former_category: '',
    attack_target: [],
    deployment: [],
    tag: [],
    signature_severity: '',
    malware_family: [],
  };
};
