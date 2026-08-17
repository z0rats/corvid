import { useRemoteConfig } from '../../../../core/hooks/useRemoteConfig';
import { ruBusinessCheckApi } from '../../services/api/ruBusinessCheckApi';

const DEFAULT_CONFIG = {
  fresh_registration_threshold_days: 365,
  history_retention_days: 90,
  small_claim_amount_threshold: 100_000,
  large_claim_amount_threshold: 1_000_000,
  multiple_claims_defendant_threshold: 3,
  mass_address_threshold: 10,
};

export function useRuBusinessCheckSettings() {
  return useRemoteConfig(ruBusinessCheckApi.getConfig, ruBusinessCheckApi.updateConfig, DEFAULT_CONFIG);
}
