import { FILE_TYPE_SIGNATURES } from '../constants/yaraConstants';
import { exportAsFile, safeFileBase } from '../../shared/utils/ruleUtils';

// Text strings and meta values are literal: escape what YARA's string syntax treats specially.
const escapeYaraText = (value) => String(value)
  .replace(/\\/g, '\\\\')
  .replace(/"/g, '\\"')
  .replace(/\n/g, '\\n')
  .replace(/\t/g, '\\t');

// Accept a regex typed with its own delimiters ("/evil[0-9]+/i", as the placeholder shows)
// as well as a bare pattern, without wrapping it in a second pair of slashes.
const splitRegex = (value) => {
  const match = /^\/(.*)\/([is]*)$/s.exec(value);
  return match ? { body: match[1], flags: match[2] } : { body: value, flags: '' };
};

export const generateYaraRule = (metadata, strings, conditions, tags) => {
  let rule = `rule ${metadata.ruleName.replace(/\s+/g, '_')}`;

  if (tags.length > 0) {
    rule += ` : ${tags.map(tag => tag.value).join(' ')}`;
  }

  rule += ' {\n';

  // Metadata section
  rule += '  meta:\n';
  Object.entries(metadata).forEach(([key, value]) => {
    if (value) {
      rule += `    ${key} = "${escapeYaraText(value)}"\n`;
    }
  });

  // Strings section
  if (strings.length > 0) {
    rule += '\n  strings:\n';
    strings.forEach(s => {
      const modifierStr = s.modifiers.length > 0 ? ` ${s.modifiers.join(' ')}` : '';
      if (s.type === 'hex') {
        rule += `    $${s.identifier} = { ${s.value} }${modifierStr}\n`;
      } else if (s.type === 'regex') {
        const { body, flags } = splitRegex(s.value);
        rule += `    $${s.identifier} = /${body}/${flags}${modifierStr}\n`;
      } else {
        rule += `    $${s.identifier} = "${escapeYaraText(s.value)}"${modifierStr}\n`;
      }
    });
  }

  // Condition section
  rule += '\n  condition:\n';
  const conditionStr = buildConditionString(conditions);
  rule += `    ${conditionStr}\n`;
  rule += '}';

  return rule;
};

export const buildConditionString = (conditions) => {
  const conditionParts = [];

  if (conditions.all) {
    conditionParts.push('all of them');
  } else if (conditions.any) {
    conditionParts.push('any of them');
  }

  if (conditions.filesize) {
    conditionParts.push(`filesize < ${conditions.filesize}KB`);
  }

  if (conditions.filetype) {
    const signature = FILE_TYPE_SIGNATURES[conditions.filetype];
    if (signature) {
      conditionParts.push(`uint16(0) == 0x${signature}`);
    }
  }

  return conditionParts.length > 0 ? conditionParts.join(' and ') : 'true';
};

export const exportYaraRule = (rule, filename) => {
  exportAsFile(rule, `${safeFileBase(filename)}.yar`);
};
