import { generateUUIDv4, getCurrentDate, exportAsFile, validateRequiredFields, safeFileBase } from '../../shared/utils/ruleUtils';

// Plain YAML only for simple word-like values; anything else (": ", "#", quotes, leading
// indicators, ...) is single-quoted, with embedded quotes doubled.
const PLAIN_SCALAR = /^[A-Za-z0-9_][\w./@()-]*( [\w./@()-]+)*$/;
export const yamlScalar = (value) => {
  const text = String(value);
  return PLAIN_SCALAR.test(text) && !/^(true|false|null|yes|no|on|off|~)$/i.test(text)
    ? text
    : `'${text.replace(/'/g, "''")}'`;
};

const yamlList = (key, items) => (
  items.length > 0 ? `${key}:\n${items.map((item) => `  - ${yamlScalar(item.value)}\n`).join('')}` : ''
);

/**
 * The detection condition: a typed custom expression wins; otherwise the chosen
 * combinator is applied to the search identifiers actually present.
 */
export const buildSigmaCondition = (detections, identifiers) => {
  const custom = detections.filter?.trim();
  if (custom) return custom;
  if (identifiers.length === 0) return null;
  switch (detections.condition) {
    case 'any':
      return identifiers.join(' or ');
    case '1 of them':
    case 'all of them':
      return detections.condition;
    default:
      return identifiers.join(' and ');
  }
};

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

  const enumValue = (value) => (value && value !== 'None' ? value.toLowerCase() : null);

  let rule = `title: ${yamlScalar(metadata.title)}\n`;
  rule += `id: ${yamlScalar(metadata.id)}\n`;
  const status = enumValue(metadata.status);
  if (status) rule += `status: ${status}\n`;
  if (metadata.description) rule += `description: ${yamlScalar(metadata.description)}\n`;
  rule += yamlList('references', references);
  if (metadata.authors.length > 0) {
    rule += `author: ${yamlScalar(metadata.authors.map((author) => author.value).join(', '))}\n`;
  }
  if (metadata.date) rule += `date: ${metadata.date}\n`;
  if (metadata.modified) rule += `modified: ${metadata.modified}\n`;
  rule += yamlList('tags', tags);

  rule += `logsource:\n`;
  for (const key of ['product', 'category', 'service', 'definition']) {
    if (logSource[key]) rule += `  ${key}: ${yamlScalar(logSource[key])}\n`;
  }

  rule += `detection:\n`;
  const identifiers = [];
  if (conditionsList.length > 0) {
    identifiers.push('selection');
    // One key per field|modifier; repeated keys become a value list (OR), since YAML keys are unique
    const grouped = new Map();
    conditionsList.forEach((cond) => {
      const key = cond.modifier && cond.modifier !== 'equals' ? `${cond.field}|${cond.modifier}` : cond.field;
      grouped.set(key, [...(grouped.get(key) || []), cond.value]);
    });
    rule += `  selection:\n`;
    grouped.forEach((values, key) => {
      if (values.length === 1) {
        rule += `    ${key}: ${yamlScalar(values[0])}\n`;
      } else {
        rule += `    ${key}:\n${values.map((v) => `      - ${yamlScalar(v)}\n`).join('')}`;
      }
    });
  }
  const keywords = detections.keywords || [];
  if (keywords.length > 0) {
    identifiers.push('keywords');
    rule += `  keywords:\n${keywords.map((k) => `    - ${yamlScalar(k.value)}\n`).join('')}`;
  }
  const condition = buildSigmaCondition(detections, identifiers);
  if (condition) rule += `  condition: ${condition}\n`;
  if (detections.timeframe) rule += `  timeframe: ${detections.timeframe}\n`;

  rule += yamlList('fields', fields);
  rule += yamlList('falsepositives', falsePositives);
  const level = enumValue(metadata.level);
  if (level) rule += `level: ${level}\n`;
  if (metadata.license) rule += `license: ${yamlScalar(metadata.license)}\n`;

  return rule;
};

/**
 * Export Sigma rule as YAML file
 * @param {string} rule - Generated rule content
 * @param {string} title - Rule title for filename
 */
export const exportSigmaRule = (rule, title) => {
  const filename = `${safeFileBase(title)}.yml`;
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
  keywords: [],
  filter: '',
  condition: 'all',
  timeframe: '',
});
