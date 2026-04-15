/**
 * Validates a string identifier for uniqueness and format
 */
export const validateStringIdentifier = (identifier, existingStrings) => {
  if (!identifier.trim()) {
    return { isValid: false, error: 'Identifier is required' };
  }

  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(identifier.trim())) {
    return {
      isValid: false,
      error: 'Identifier must start with a letter or underscore and contain only letters, numbers, and underscores',
    };
  }

  if (existingStrings.some(s => s.identifier === identifier.trim())) {
    return { isValid: false, error: 'Identifier must be unique' };
  }

  return { isValid: true, error: null };
};

/**
 * Validates string value based on its type
 */
export const validateStringValue = (value, type) => {
  if (!value.trim()) {
    return { isValid: false, error: 'Value is required' };
  }

  switch (type) {
    case 'hex':
      if (!/^[0-9a-fA-F\s]+$/.test(value.trim())) {
        return { isValid: false, error: 'Hex value must contain only hexadecimal digits and spaces' };
      }
      break;
    case 'regex':
      try {
        new RegExp(value.trim());
      } catch (e) {
        return { isValid: false, error: 'Invalid regular expression' };
      }
      break;
    default:
      if (value.trim().length === 0) {
        return { isValid: false, error: 'Value cannot be empty' };
      }
  }

  return { isValid: true, error: null };
};

/**
 * Validates rule name for YARA compliance
 */
export const validateRuleName = (ruleName) => {
  if (!ruleName.trim()) {
    return { isValid: false, error: 'Rule name is required' };
  }

  const cleanName = ruleName.replace(/\s+/g, '_');
  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(cleanName)) {
    return {
      isValid: false,
      error: 'Rule name must start with a letter or underscore and contain only letters, numbers, underscores, and spaces',
    };
  }

  return { isValid: true, error: null };
};

/**
 * Formats a string for display in the UI
 */
export const formatStringForDisplay = (string) => {
  const modifierStr = string.modifiers.length > 0 ? ` | Modifiers: ${string.modifiers.join(', ')}` : '';
  return `$${string.identifier} (${string.type.toUpperCase()})${modifierStr}: ${string.value}`;
};

/**
 * Sanitizes input to prevent XSS and other security issues
 */
export const sanitizeInput = (input) => {
  if (typeof input !== 'string') return '';
  return input.replace(/[<>]/g, '');
};
