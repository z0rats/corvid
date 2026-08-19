import {
  getTierColor,
  generateKeyDisplayName,
  calculateCompletionPercentage,
  getConfiguredCount,
  filterServices,
  formatModuleName,
} from './settingsUtils';

describe('getTierColor', () => {
  const theme = {
    palette: {
      success: { main: '#4caf50' },
      error: { main: '#f44336' },
      warning: { main: '#ff9800' },
      text: { disabled: '#616161' },
    },
  };

  it('resolves a known tier to its palette color', () => {
    expect(getTierColor('free', theme)).toBe('#4caf50');
    expect(getTierColor('paid', theme)).toBe('#f44336');
    expect(getTierColor('freemium', theme)).toBe('#ff9800');
  });

  it('falls back to the disabled text color for an unknown tier', () => {
    expect(getTierColor('unknown', theme)).toBe('#616161');
  });

  it('falls back to a hardcoded gray when no theme is given', () => {
    expect(getTierColor('free', null)).toBe('#616161');
  });
});

describe('generateKeyDisplayName', () => {
  it('title-cases an underscore-separated key name by default', () => {
    expect(generateKeyDisplayName('some_api_key', 'Service')).toBe('Service API Key');
  });

  it('labels a client_id key with the service name', () => {
    expect(generateKeyDisplayName('client_id', 'Google')).toBe('Google Client ID');
  });

  it('labels a client_secret key with the service name', () => {
    expect(generateKeyDisplayName('client_secret', 'Google')).toBe('Google Client Secret');
  });

  it('labels a pat key as a Personal Access Token', () => {
    expect(generateKeyDisplayName('github_pat', 'GitHub')).toBe('GitHub Personal Access Token');
  });

  it('labels a bearer key as a Bearer Token', () => {
    expect(generateKeyDisplayName('bearer_token', 'Service')).toBe('Service Bearer Token');
  });

  it('falls back to a title-cased key name for a plain key', () => {
    expect(generateKeyDisplayName('key', 'Service')).toBe('Key');
  });
});

describe('calculateCompletionPercentage', () => {
  it('returns 0 for an empty config', () => {
    expect(calculateCompletionPercentage({})).toBe(0);
  });

  it('rounds the percentage of available services', () => {
    const config = {
      a: { available: true },
      b: { available: true },
      c: { available: false },
    };
    expect(calculateCompletionPercentage(config)).toBe(67);
  });

  it('returns 100 when every service is available', () => {
    const config = { a: { available: true }, b: { available: true } };
    expect(calculateCompletionPercentage(config)).toBe(100);
  });
});

describe('getConfiguredCount', () => {
  it('counts only available services', () => {
    const config = {
      a: { available: true },
      b: { available: false },
      c: { available: true },
    };
    expect(getConfiguredCount(config)).toBe(2);
  });

  it('returns 0 for an empty config', () => {
    expect(getConfiguredCount({})).toBe(0);
  });
});

describe('filterServices', () => {
  const config = {
    abuseipdb: { name: 'AbuseIPDB', available: true },
    virustotal: { name: 'VirusTotal', available: false },
    shodan: { name: 'Shodan', available: true },
  };

  it('filters by case-insensitive name search', () => {
    const result = filterServices(config, 'shod', false);
    expect(result.map(([key]) => key)).toEqual(['shodan']);
  });

  it('filters to only configured services when requested', () => {
    const result = filterServices(config, '', true);
    expect(result.map(([key]) => key).sort()).toEqual(['abuseipdb', 'shodan']);
  });

  it('sorts results alphabetically by service name', () => {
    const result = filterServices(config, '', false);
    expect(result.map(([, service]) => service.name)).toEqual(['AbuseIPDB', 'Shodan', 'VirusTotal']);
  });

  it('combines search and configured filters', () => {
    const result = filterServices(config, 'virustotal', true);
    expect(result).toEqual([]);
  });
});

describe('formatModuleName', () => {
  it.each([
    ['ioc_tools', 'IOC Tools'],
    ['cvss_calculator', 'CVSS Calculator'],
    ['llm_templates', 'AI Templates'],
    ['rule_creator', 'Detection Rules'],
    ['email_analyzer', 'Email Analyzer'],
    ['newsfeed', 'Newsfeed'],
  ])('formats %s as %s', (name, expected) => {
    expect(formatModuleName(name)).toBe(expected);
  });
});
