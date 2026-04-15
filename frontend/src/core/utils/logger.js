const isDevelopment = process.env.NODE_ENV === 'development';

function createLogger(prefix = 'APP') {
  return {
    debug(message, ...args) {
      if (isDevelopment) {
        console.debug(`[${prefix}] ${message}`, ...args);
      }
    },

    info(message, ...args) {
      if (isDevelopment) {
        console.info(`[${prefix}] ${message}`, ...args);
      }
    },

    warn(message, ...args) {
      if (isDevelopment) {
        console.warn(`[${prefix}] ${message}`, ...args);
      }
    },

    error(message, ...args) {
      if (isDevelopment) {
        console.error(`[${prefix}] ${message}`, ...args);
      }
    },
  };
}

export const logger = createLogger();
export { createLogger };
