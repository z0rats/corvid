import { TIER_PALETTE_KEYS, TIER_LABELS } from '../constants/settingsConstants';

/**
 * Get color for a tier chip from theme palette
 */
export function getTierColor(tier, theme) {
  const paletteKey = TIER_PALETTE_KEYS[tier];
  if (paletteKey && theme) {
    return theme.palette[paletteKey].main;
  }
  return theme?.palette?.text?.disabled || '#616161';
}

/**
 * Get label for a tier
 */
export function getTierLabel(tier) {
  return TIER_LABELS[tier] || tier;
}

/**
 * Generate display name for API key
 */
export function generateKeyDisplayName(keyName, serviceName) {
  let keyDisplayName = keyName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase());

  if (keyName.includes('client_id')) keyDisplayName = `${serviceName} Client ID`;
  if (keyName.includes('client_secret')) keyDisplayName = `${serviceName} Client Secret`;
  if (keyName.includes('api_key')) keyDisplayName = `${serviceName} API Key`;
  if (keyName.includes('pat')) keyDisplayName = `${serviceName} Personal Access Token`;
  if (keyName.includes('bearer')) keyDisplayName = `${serviceName} Bearer Token`;

  return keyDisplayName;
}

/**
 * Calculate completion percentage for services
 */
export function calculateCompletionPercentage(servicesConfig) {
  const totalServices = Object.keys(servicesConfig).length;
  if (totalServices === 0) return 0;

  const configuredServices = Object.values(servicesConfig).reduce((count, service) => {
    return count + (service.available ? 1 : 0);
  }, 0);

  return Math.round((configuredServices / totalServices) * 100);
}

/**
 * Get configured services count
 */
export function getConfiguredCount(servicesConfig) {
  return Object.values(servicesConfig).reduce((count, service) => {
    return count + (service.available ? 1 : 0);
  }, 0);
}

/**
 * Filter services based on search and configuration status
 */
export function filterServices(servicesConfig, searchFilter, showOnlyConfigured) {
  return Object.entries(servicesConfig)
    .filter(([key, service]) => {
      const matchesSearch = service.name.toLowerCase().includes(searchFilter.toLowerCase());
      const matchesFilter = !showOnlyConfigured || service.available;
      return matchesSearch && matchesFilter;
    })
    .sort(([, a], [, b]) => a.name.localeCompare(b.name));
}

/**
 * Format module name for display
 * Converts internal names like 'ioc_tools' to 'IOC Tools'
 */
export function formatModuleName(name) {
  const specialCases = {
    'ioc': 'IOC',
    'cvss': 'CVSS',
    'llm': 'AI',
    'ai': 'AI',
  };

  return name
    .split('_')
    .map(word => {
      const lowerWord = word.toLowerCase();
      if (specialCases[lowerWord]) {
        return specialCases[lowerWord];
      }
      if (lowerWord === 'creator') {
        return 'Rules';
      }
      if (lowerWord === 'rule') {
        return 'Detection';
      }
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(' ');
}
