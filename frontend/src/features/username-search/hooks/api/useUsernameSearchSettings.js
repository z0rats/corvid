import { useRemoteConfig } from '../../../../core/hooks/useRemoteConfig';
import { usernameSearchApi } from '../../services/api/usernameSearchApi';

const DEFAULT_CONFIG = {
  timeout_seconds: 30,
  max_concurrency: 100,
  top_sites_count: 500,
  proxy_url: '',
  auto_update_db_enabled: true,
  auto_update_interval_hours: 24,
  db_last_updated_at: null,
  db_site_count: 0,
  latest_pypi_version: null,
  pypi_checked_at: null,
};

export function useUsernameSearchSettings() {
  return useRemoteConfig(usernameSearchApi.getConfig, usernameSearchApi.updateConfig, DEFAULT_CONFIG);
}
