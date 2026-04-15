/**
 * Generate a UUID v4
 * @returns {string} UUID v4 string
 */
export const generateUUIDv4 = () => crypto.randomUUID();

/**
 * Get current date in YYYY-MM-DD format
 * @returns {string} Current date
 */
export const getCurrentDate = () => {
  return new Date().toISOString().split('T')[0];
};

/**
 * Generate a random SID for Snort rules
 * @returns {number} 6-digit SID
 */
export const generateSID = () => {
  return Math.floor(Math.random() * 900000) + 100000;
};

/**
 * Export content as a file
 * @param {string} content - Content to export
 * @param {string} filename - Name of the file
 * @param {string} mimeType - MIME type of the file
 */
export const exportAsFile = (content, filename, mimeType = 'text/plain') => {
  const blob = new Blob([content], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  window.URL.revokeObjectURL(url);
};

/**
 * Validate required fields
 * @param {Object} fields - Object with field names as keys and values
 * @param {string[]} requiredFields - Array of required field names
 * @returns {string[]} Array of error messages
 */
export const validateRequiredFields = (fields, requiredFields) => {
  const errors = [];
  
  requiredFields.forEach(fieldName => {
    const value = fields[fieldName];
    if (!value || (typeof value === 'string' && !value.trim())) {
      errors.push(`${fieldName} is required`);
    }
  });
  
  return errors;
};
