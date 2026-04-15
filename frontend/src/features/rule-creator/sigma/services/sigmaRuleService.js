import { generateUUIDv4, getCurrentDate, exportAsFile, validateRequiredFields } from '../../shared/utils/ruleUtils';

/**
 * Generate a complete Sigma rule string
 * @param {Object} metadata - Rule metadata
 * @param {Object} logSource - Log source configuration
 * @param {Array} conditionsList - Detection conditions
 * @param {Object} detections - Detection settings
 * @param {Array} fields - Rule fields
 * @param {Array} references - Rule references
 * @param {Array} tags - Rule tags
 * @param {Array} falsePositives - False positives
 * @returns {string} Generated Sigma rule
 */
export const generateSigmaRule = (
  metadata,
  logSource,
  conditionsList,
  detections,
  fields,
  references,
  tags,
  falsePositives
) => {
  const validationErrors = validateRequiredFields(metadata, ['title', 'id']);
  if (validationErrors.length > 0) {
    throw new Error(validationErrors.join(', '));
  }

  let rule = `title: ${metadata.title}\n`;
  rule += `id: ${metadata.id}\n`;
  rule += `status: ${metadata.status}\n`;
  
  if (metadata.description) rule += `description: ${metadata.description}\n`;
  
  if (metadata.authors.length > 0) {
    rule += `authors:\n`;
    metadata.authors.forEach(author => {
      rule += `  - ${author.value}\n`;
    });
  }
  
  if (metadata.date) rule += `date: ${metadata.date}\n`;
  if (metadata.modified) rule += `modified: ${metadata.modified}\n`;
  if (metadata.license) rule += `license: ${metadata.license}\n`;
  
  rule += `level: ${metadata.level}\n`;
  
  if (tags.length > 0) {
    rule += `tags:\n`;
    tags.forEach(tag => {
      rule += `  - ${tag.value}\n`;
    });
  }

  if (references.length > 0) {
    rule += `references:\n`;
    references.forEach(ref => {
      rule += `  - ${ref.value}\n`;
    });
  }

  if (falsePositives.length > 0) {
    rule += `falsepositives:\n`;
    falsePositives.forEach(fp => {
      rule += `  - ${fp.value}\n`;
    });
  }
  
  rule += `logsource:\n`;
  if (logSource.product) rule += `  product: ${logSource.product}\n`;
  if (logSource.category) rule += `  category: ${logSource.category}\n`;
  if (logSource.service) rule += `  service: ${logSource.service}\n`;
  if (logSource.definition) rule += `  definition: ${logSource.definition}\n`;
  
  rule += `detection:\n`;

  if (conditionsList.length > 0 || detections.filter || detections.timeframe) {
    if (conditionsList.length > 0) {
      rule += `  selection:\n`;
      conditionsList.forEach(cond => {
        if (cond.modifier !== 'equals') {
          rule += `    ${cond.field}|${cond.modifier} ${cond.modifier === 're' ? '' : cond.modifier} "${cond.value}"\n`;
        } else {
          rule += `    ${cond.field} ${cond.modifier} "${cond.value}"\n`;
        }
      });
    }
    
    if (detections.filter) {
      rule += `  filter:\n    ${detections.filter}\n`;
    }
    
    if (detections.condition) {
      rule += `  condition: ${detections.condition}\n`;
    }
    
    if (detections.timeframe) {
      rule += `  timeframe: ${detections.timeframe}\n`;
    }
  }

  if (fields.length > 0) {
    rule += `fields:\n`;
    fields.forEach(field => {
      rule += `  - ${field.value}\n`;
    });
  }

  return rule;
};

/**
 * Export Sigma rule as YAML file
 * @param {string} rule - Generated rule content
 * @param {string} title - Rule title for filename
 */
export const exportSigmaRule = (rule, title) => {
  const filename = `${title.replace(/\s+/g, '_')}.yml`;
  exportAsFile(rule, filename);
};

/**
 * Create initial metadata with generated UUID and current date
 * @returns {Object} Initial metadata object
 */
export const createInitialMetadata = () => ({
  title: '',
  id: generateUUIDv4(),
  description: '',
  authors: [],
  date: getCurrentDate(),
  modified: '',
  level: 'None',
  license: '',
  status: 'None',
});

/**
 * Create initial log source configuration
 * @returns {Object} Initial log source object
 */
export const createInitialLogSource = () => ({
  product: '',
  category: '',
  service: '',
  definition: '',
});

/**
 * Create initial detection configuration
 * @returns {Object} Initial detection object
 */
export const createInitialDetection = () => ({
  selection: [],
  filter: '',
  condition: 'all',
  timeframe: '',
});
