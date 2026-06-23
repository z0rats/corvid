export const FONT_OPTIONS = [
  { value: 'Poppins', label: 'Poppins' },
  { value: 'Nunito', label: 'Nunito' },
  { value: 'Roboto', label: 'Roboto' },
  { value: 'Arial', label: 'Arial' },
  { value: 'Helvetica', label: 'Helvetica' },
  { value: 'Aldrich', label: 'Aldrich' },
];

export const NOTIFICATION_MESSAGES = {
  API_KEY_SAVED: 'API key configured successfully.',
  API_KEY_REMOVED: 'API key removed successfully.',
  API_KEY_ACTIVATED: 'service activated successfully.',
  API_KEY_DEACTIVATED: 'service deactivated successfully.',
  FONT_UPDATED: 'Font updated successfully.',
  DARKMODE_UPDATED: 'Dark mode updated successfully.',
  MODULE_ENABLED: 'Module enabled successfully.',
  MODULE_DISABLED: 'Module disabled successfully.',
  LOAD_ERROR: 'Failed to load configuration.',
  SAVE_ERROR: 'Failed to save changes.',
  INVALID_API_KEY: 'Please enter a valid API key.',
};

export const TIER_PALETTE_KEYS = {
  free: 'success',
  paid: 'error',
  freemium: 'warning',
};

export const TIER_LABELS = {
  free: 'Free',
  paid: 'Paid',
  freemium: 'Freemium',
};

export const VALID_MODULE_IDS = [
  'newsfeed',
  'ioc_tools',
  'email_analyzer',
  'image_tools',
  'llm_templates',
  'cvss_calculator',
  'rule_creator',
];

export const MODULE_DESCRIPTIONS = {
  newsfeed: 'Aggregate and browse cybersecurity news from RSS feeds.',
  ioc_tools: 'Look up, extract, and analyze indicators of compromise.',
  email_analyzer: 'Parse and inspect email headers and content.',
  image_tools: 'View EXIF/GPS metadata and run reverse image searches.',
  llm_templates: 'Create and run AI-powered analysis templates.',
  cvss_calculator: 'Calculate CVSS 3.1 and 4.0 vulnerability scores.',
  rule_creator: 'Build Sigma, YARA, and Snort detection rules.',
};
