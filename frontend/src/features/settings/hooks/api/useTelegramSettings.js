import { useCallback, useEffect, useState } from 'react';
import { settingsApi } from '../../services/api/settingsApi';

function errorMessage(err, fallback) {
  return err.response?.data?.detail || err.message || fallback;
}

/**
 * Hook for the Telegram notification settings tab: fetches the singleton
 * settings row on mount, and exposes separate loading flags for saving a
 * field vs sending a test message (a user could plausibly wait on one
 * without the other button appearing busy too - same reasoning as useBackup).
 */
export function useTelegramSettings() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    settingsApi.getTelegramSettings()
      .then((data) => {
        if (!cancelled) setSettings(data);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const updateSettings = useCallback(async (update, fallbackMessage) => {
    setSaving(true);
    try {
      const updated = await settingsApi.updateTelegramSettings(update);
      setSettings(updated);
      return { success: true };
    } catch (err) {
      return { success: false, message: errorMessage(err, fallbackMessage) };
    } finally {
      setSaving(false);
    }
  }, []);

  const sendTestMessage = useCallback(async (fallbackMessage) => {
    setTesting(true);
    try {
      const result = await settingsApi.sendTelegramTestMessage();
      return { success: true, message: result.message };
    } catch (err) {
      return { success: false, message: errorMessage(err, fallbackMessage) };
    } finally {
      setTesting(false);
    }
  }, []);

  return { settings, loading, saving, testing, updateSettings, sendTestMessage };
}
