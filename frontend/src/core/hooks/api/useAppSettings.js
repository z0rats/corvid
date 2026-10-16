import { useEffect } from 'react';
import { useSetAtom } from 'jotai';
import { settingsService } from '../../services/api/settingsService';
import { createLogger } from '../../utils/logger';
import i18n, { SUPPORTED_LANGUAGES } from '../../i18n';
import {
  apiKeysState,
  modulesState,
  generalSettingsState,
  aiSettingsState,
  hasLocalLlmState,
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
  const setHasLocalLlm = useSetAtom(hasLocalLlmState);

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

        if (SUPPORTED_LANGUAGES.includes(generalSettingsResponse.language)) {
          i18n.changeLanguage(generalSettingsResponse.language);
        }
      } catch (error) {
        if (!ignore) {
          logger.error('Error fetching app settings:', error);
        }
      }
    };

    // Separate from the batch above: probing Ollama is best-effort and must not
    // take the other settings down with it.
    const fetchLocalLlmAvailability = async () => {
      try {
        const { models = [] } = await settingsService.getAvailableModels();
        if (!ignore) setHasLocalLlm(models.some((model) => model.id.startsWith('ollama:')));
      } catch (error) {
        if (!ignore) logger.warn('Could not check for local LLM models:', error);
      }
    };

    fetchAppSettings();
    fetchLocalLlmAvailability();
    return () => { ignore = true; };
  }, [setApiKeys, setGeneralSettings, setModules, setAiSettings, setHasLocalLlm]);
}
