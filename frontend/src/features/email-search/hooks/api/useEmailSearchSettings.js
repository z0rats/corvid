import { useRemoteConfig } from '../../../../core/hooks/useRemoteConfig';
import { emailSearchApi } from '../../services/api/emailSearchApi';

const DEFAULT_CONFIG = {
  timeout_seconds: 10,
  max_concurrency: 10,
  proxy_url: '',
  use_tor: false,
  enable_smtp_checks: false,
  enable_headless_checks: false,
  latest_pypi_version: null,
  pypi_checked_at: null,
};

export function useEmailSearchSettings() {
  return useRemoteConfig(emailSearchApi.getConfig, emailSearchApi.updateConfig, DEFAULT_CONFIG);
}
