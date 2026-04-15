import { FILE_TYPE_SIGNATURES } from '../constants/yaraConstants';
import { exportAsFile } from '../../shared/utils/ruleUtils';

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
      rule += `    ${key} = "${value}"\n`;
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
        rule += `    $${s.identifier} = /${s.value}/${modifierStr}\n`;
      } else {
        rule += `    $${s.identifier} = "${s.value}"${modifierStr}\n`;
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
  exportAsFile(rule, `${filename.replace(/\s+/g, '_')}.yar`);
};
