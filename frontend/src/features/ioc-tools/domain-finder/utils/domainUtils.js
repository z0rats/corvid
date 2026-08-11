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
  },

  // Mirrors backend's sanitize_domain_input (domain_finder/utils/validation_utils.py)
  // so a pasted URL like "https://example.com/path" resolves to "example.com" before
  // it gets interpolated into any /api/domain/*/{domain} path.
  normalizeDomainInput(input) {
    if (!input || typeof input !== 'string') {
      return '';
    }

    const raw = input.trim().toLowerCase();
    if (!raw) return '';

    // Search patterns (wildcards) are passed through untouched, same as the backend.
    if (raw.includes('*') || raw.includes('?')) {
      return raw;
    }

    let domain = raw;
    if (domain.startsWith('http://') || domain.startsWith('https://')) {
      try {
        domain = new URL(domain).hostname || domain.split('://', 2)[1] || domain;
      } catch {
        domain = domain.split('://', 2)[1] || domain;
      }
    }

    domain = domain.split('/')[0].split('#')[0];

    if (domain.includes(':') && (domain.match(/:/g) || []).length === 1) {
      domain = domain.split(':')[0];
    }

    return domain;
  }
};
