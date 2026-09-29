import { useRemoteConfig } from '../../../../core/hooks/useRemoteConfig';
import { phoneSearchApi } from '../../services/api/phoneSearchApi';

const DEFAULT_CONFIG = {
  timeout_seconds: 10,
  proxy_url: '',
};

export function usePhoneSearchSettings() {
  return useRemoteConfig(phoneSearchApi.getConfig, phoneSearchApi.updateConfig, DEFAULT_CONFIG);
}
