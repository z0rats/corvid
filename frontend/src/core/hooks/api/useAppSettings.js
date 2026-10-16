import { useEffect, useRef } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';
import { settingsService } from '../../services/api/settingsService';
import { createLogger } from '../../utils/logger';
import i18n, { SUPPORTED_LANGUAGES } from '../../i18n';
import {
  apiKeysState,
  modulesState,
  generalSettingsState,
  aiSettingsState,
  availableLlmModelsState,
} from '../../state/atoms';
import { LLM_MODELS_REPROBE_EVENT } from '../../utils/llmModelsReprobe';

const logger = createLogger('AppSettings');

export const LLM_REPROBE_MIN_INTERVAL_MS = 30_000;

// Which LLM provider keys are present - a change means the backend's model registry changed.
const llmKeySignature = (keys) => `${Boolean(keys?.openai)}:${Boolean(keys?.anthropic)}`;

/**
 * Hook for fetching and managing application settings data
 */
export function useAppSettings() {
  const setApiKeys = useSetAtom(apiKeysState);
  const setModules = useSetAtom(modulesState);
  const setGeneralSettings = useSetAtom(generalSettingsState);
  const setAiSettings = useSetAtom(aiSettingsState);
  const setAvailableLlmModels = useSetAtom(availableLlmModelsState);
  const apiKeys = useAtomValue(apiKeysState);
  // Set by the mount effect below; the key-change effect calls the same probe.
  const probeLlmModels = useRef(null);
  // Signature of the keys the registry was last probed for; null until the settings batch has
  // loaded, so the initial `{}` -> loaded-keys transition isn't mistaken for a key being saved.
  const probedKeySignature = useRef(null);

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

        probedKeySignature.current = llmKeySignature(apikeysResponse);
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

    // Separate from the batch above: probing the model registry (which reaches out to a local
    // Ollama server) is best-effort and must not take the other settings down with it. Probes
    // can overlap (load, tab focus, a key saved), so only the newest one may write.
    let lastProbeAt = 0;
    let latestProbe = 0;
    const fetchLlmAvailability = async () => {
      const probe = ++latestProbe;
      lastProbeAt = Date.now();
      try {
        const { models = [] } = await settingsService.getAvailableModels();
        if (!ignore && probe === latestProbe) setAvailableLlmModels(models);
      } catch (error) {
        if (!ignore) logger.warn('Could not check for available LLM models:', error);
      }
    };
    probeLlmModels.current = fetchLlmAvailability;

    // Re-probe when the tab regains focus, so starting Ollama or pulling a model after the page
    // loaded unlocks the AI features without a reload. Throttled: each probe hits Ollama.
    const onVisible = () => {
      if (document.visibilityState === 'visible' && Date.now() - lastProbeAt >= LLM_REPROBE_MIN_INTERVAL_MS) {
        fetchLlmAvailability();
      }
    };

    fetchAppSettings();
    fetchLlmAvailability();
    document.addEventListener('visibilitychange', onVisible);
    window.addEventListener(LLM_MODELS_REPROBE_EVENT, fetchLlmAvailability);
    return () => {
      ignore = true;
      probeLlmModels.current = null;
      document.removeEventListener('visibilitychange', onVisible);
      window.removeEventListener(LLM_MODELS_REPROBE_EVENT, fetchLlmAvailability);
    };
  }, [setApiKeys, setGeneralSettings, setModules, setAiSettings, setAvailableLlmModels]);

  // Saving or removing an LLM provider key changes which models exist - re-probe at once, so the
  // AI features and the model pickers follow without waiting for a tab refocus.
  const keySignature = llmKeySignature(apiKeys);
  useEffect(() => {
    if (probedKeySignature.current === null || probedKeySignature.current === keySignature) return;
    probedKeySignature.current = keySignature;
    probeLlmModels.current?.();
  }, [keySignature]);
}
