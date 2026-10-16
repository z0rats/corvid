export const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'ru', label: 'Русский' },
];

export const NOTIFICATION_MESSAGES = {
  API_KEY_SAVED: 'API key configured successfully.',
  API_KEY_REMOVED: 'API key removed successfully.',
  API_KEY_ACTIVATED: 'service activated successfully.',
  API_KEY_DEACTIVATED: 'service deactivated successfully.',
  LANGUAGE_UPDATED: 'Language updated successfully.',
  COMMAND_PALETTE_UPDATED: 'Command palette settings updated successfully.',
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

export const VALID_MODULE_IDS = [
  'newsfeed',
  'ioc_tools',
  'email_analyzer',
  'image_tools',
  'llm_templates',
  'cvss_calculator',
  'rule_creator',
];

// Card look shared by the General and Command Palette settings tabs. `bgcolor` takes a palette
// path, so it follows the active theme without a useTheme()/useMemo per component.
export const SETTINGS_CARD_SX = {
  p: 1,
  pl: 2,
  m: 1,
  boxShadow: '0',
  bgcolor: 'background.card',
  borderRadius: 1,
};
