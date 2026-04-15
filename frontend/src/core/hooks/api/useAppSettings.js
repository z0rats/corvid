import { useEffect } from 'react';
import { useSetAtom } from 'jotai';
import { settingsService } from '../../services/api/settingsService';
import { createLogger } from '../../utils/logger';
import {
  apiKeysState,
  modulesState,
  generalSettingsState,
  aiSettingsState,
} from '../../state/atoms';

const logger = createLogger('AppSettings');

/**
 * Hook for fetching and managing application settings data
 */
export function useAppSettings() {
  const setApiKeys = useSetAtom(apiKeysState);
  const setModules = useSetAtom(modulesState);
  const setGeneralSettings = useSetAtom(generalSettingsState);
  const setAiSettings = useSetAtom(aiSettingsState);

  useEffect(() => {
    let ignore = false;

    const fetchAppSettings = async () => {
      try {
        const [
          apikeysResponse,
          modulesResponse,
          generalSettingsResponse,
          aiSettingsResponse,
        ] = await Promise.all([
          settingsService.getApiKeys(),
          settingsService.getModules(),
          settingsService.getGeneralSettings(),
          settingsService.getAiSettings(),
        ]);

        if (ignore) return;

        setApiKeys(apikeysResponse);

        const modulesData = modulesResponse.reduce((dict, item) => {
          dict[item.name] = { enabled: item.enabled };
          return dict;
        }, {});
        setModules(modulesData);

        setGeneralSettings(generalSettingsResponse);
        setAiSettings(aiSettingsResponse);
        document.body.setAttribute('data-font', generalSettingsResponse.font);
      } catch (error) {
        if (!ignore) {
          logger.error('Error fetching app settings:', error);
        }
      }
    };

    fetchAppSettings();
    return () => { ignore = true; };
  }, [setApiKeys, setGeneralSettings, setModules, setAiSettings]);
}
