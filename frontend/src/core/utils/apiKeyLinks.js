/** Settings → API Keys narrowed to one service (backend service_config.py key, e.g. 'steam'). */
export const apiKeySettingsPath = (serviceKey) => (
  serviceKey ? `/settings/apikeys?service=${encodeURIComponent(serviceKey)}` : '/settings/apikeys'
);
