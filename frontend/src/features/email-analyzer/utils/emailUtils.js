export const emailUtils = {
  extractEmailAddress: (inputString) => {
    const emailRegex = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;
    const matches = inputString.match(emailRegex);
    if (matches && matches.length > 0) {
      return matches[0];
    }
    return null;
  },

  getHashType: (hash) => {
    if (!hash) return 'MD5';
    
    const hashLength = hash.length;
    if (hashLength === 32) return 'MD5';
    if (hashLength === 40) return 'SHA1';
    if (hashLength === 64) return 'SHA256';
    return 'MD5'; // Default
  },

  formatFileSize: (bytes) => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  getWarningLevel: (tlp) => {
    switch (tlp) {
      case 'red':
        return 'error';
      case 'orange':
        return 'warning';
      case 'green':
        return 'success';
      default:
        return 'info';
    }
  }
};
