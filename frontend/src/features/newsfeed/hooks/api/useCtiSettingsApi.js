import { useState, useEffect, useCallback } from 'react';
import { newsfeedSettingsApi } from '../../services/api/settingsApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('CtiSettings');

export function useCtiSettings() {
  const [ctiSettings, setCtiSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;
    const fetchSettings = async () => {
      try {
        const response = await newsfeedSettingsApi.getCtiSettings();
        if (!ignore) {
          setCtiSettings(response.settings || {});
        }
      } catch (err) {
        if (!ignore) {
          logger.error('Error loading CTI settings:', err);
          setError(err);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };
    fetchSettings();
    return () => { ignore = true; };
  }, []);

  const handleInputChange = useCallback((category, field, value) => {
    setCtiSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [field]: value,
      },
    }));
  }, []);

  const handleAttackTypePriorityChange = useCallback((attackType, priority) => {
    setCtiSettings(prev => ({
      ...prev,
      threat_actor_and_attack_type: {
        ...prev.threat_actor_and_attack_type,
        attack_type_priorities: {
          ...(prev.threat_actor_and_attack_type?.attack_type_priorities || {}),
          [attackType]: priority,
        },
      },
    }));
  }, []);

  const saveSettings = useCallback(async () => {
    try {
      await newsfeedSettingsApi.updateCtiSettings(ctiSettings);
      return { success: true };
    } catch (err) {
      logger.error('Error saving CTI settings:', err);
      return { success: false, error: err };
    }
  }, [ctiSettings]);

  return {
    ctiSettings,
    loading,
    error,
    handleInputChange,
    handleAttackTypePriorityChange,
    saveSettings,
  };
}
