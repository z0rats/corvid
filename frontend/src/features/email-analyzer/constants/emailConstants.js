export const EMAIL_CONSTANTS = {
  ACCEPTED_FILE_TYPES: {
    'message/rfc822': ['.eml']
  },
  
  FILE_UPLOAD: {
    MAX_SIZE: 10 * 1024 * 1024, // 10MB
    ACCEPTED_EXTENSIONS: ['.eml']
  },

  HASH_TYPES: {
    MD5: 'MD5',
    SHA1: 'SHA1',
    SHA256: 'SHA256'
  },

  WARNING_LEVELS: {
    RED: 'red',
    ORANGE: 'orange', 
    GREEN: 'green',
    INFO: 'info'
  },

  ALERT_SEVERITIES: {
    ERROR: 'error',
    WARNING: 'warning',
    SUCCESS: 'success',
    INFO: 'info'
  },

  IOC_TYPES: {
    EMAIL: 'Email',
    HASH: 'Hash',
    URL: 'URL',
    IP: 'IP',
    DOMAIN: 'Domain'
  }
};
