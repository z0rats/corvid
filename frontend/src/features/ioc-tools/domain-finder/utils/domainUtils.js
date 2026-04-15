export const domainUtils = {
  getStatusColor(status) {
    if (!status) return 'darkgrey';
    const statusStr = String(status);
    if (statusStr.startsWith('2')) return 'green';
    if (statusStr.startsWith('4')) return 'orange';
    if (statusStr.startsWith('5')) return 'red';
    return 'darkgrey';
  },

  formatDate(dateString) {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return dateString;
    }
  },

  validateDomainPattern(pattern) {
    if (!pattern || typeof pattern !== 'string') {
      return false;
    }
    return pattern.trim().length > 0;
  }
};
