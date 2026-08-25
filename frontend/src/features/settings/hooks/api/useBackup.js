import { useCallback, useState } from 'react';
import { settingsApi } from '../../services/api/settingsApi';

function errorMessage(err, fallback) {
  return err.response?.data?.detail || err.message || fallback;
}

/**
 * Hook for the full-app backup/restore API operations (export download, restore
 * upload). Export and restore get separate loading flags since a user could
 * plausibly want to see one card's state without the other appearing busy too.
 */
export function useBackup() {
  const [exporting, setExporting] = useState(false);
  const [restoring, setRestoring] = useState(false);

  const getStatus = useCallback(async () => {
    return settingsApi.getBackupStatus();
  }, []);

  const exportBackup = useCallback(async ({ includeAccessToken, passphrase }, fallbackMessage) => {
    setExporting(true);
    try {
      const { blob, filename } = await settingsApi.exportBackup({ includeAccessToken, passphrase });
      return { success: true, blob, filename };
    } catch (err) {
      return { success: false, message: errorMessage(err, fallbackMessage) };
    } finally {
      setExporting(false);
    }
  }, []);

  const restoreBackup = useCallback(async ({ file, passphrase }, fallbackMessage) => {
    setRestoring(true);
    try {
      const result = await settingsApi.restoreBackup({ file, passphrase });
      return { success: true, ...result };
    } catch (err) {
      return { success: false, message: errorMessage(err, fallbackMessage) };
    } finally {
      setRestoring(false);
    }
  }, []);

  return { exporting, restoring, getStatus, exportBackup, restoreBackup };
}
