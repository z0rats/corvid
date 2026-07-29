import { useRemoteConfig } from '../../../../core/hooks/useRemoteConfig';
import { usernameSearchApi } from '../../services/api/usernameSearchApi';

const DEFAULT_CONFIG = {
  timeout_seconds: 0,
  top_sites_count: 0,
  latest_pypi_version: null,
  pypi_checked_at: null,
};

export function useSocialAnalyzerSettings() {
  return useRemoteConfig(usernameSearchApi.getSocialAnalyzerConfig, usernameSearchApi.updateSocialAnalyzerConfig, DEFAULT_CONFIG);
}
