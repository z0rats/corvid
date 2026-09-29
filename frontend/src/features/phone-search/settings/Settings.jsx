import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import Skeleton from '@mui/material/Skeleton';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import { usePhoneSearchSettings } from '../hooks/api/usePhoneSearchSettings';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import AppSnackbar from '../../../core/components/ui/AppSnackbar';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('PhoneSearchSettings');

export default function Settings() {
  const { t } = useTranslation('phoneSearch');
  const { config, loading, saving, updateConfig } = usePhoneSearchSettings();
  const { notification, showSuccess, showError, hideNotification } = useNotification();

  const handleError = useCallback((error) => {
    logger.error('Settings error:', error);
    showError(error.response?.data?.detail || error.message || t('settings.updateError'));
  }, [showError, t]);

  const handleChange = useCallback(async (field, value) => {
    const result = await updateConfig({ [field]: value });
    if (result.success) {
      showSuccess(t('settings.updateSuccess'));
    } else {
      handleError(result.error);
    }
  }, [updateConfig, showSuccess, handleError, t]);

  if (loading) {
    return (
      <Card sx={{ p: 3 }}>
        <Skeleton variant="rectangular" height={200} />
      </Card>
    );
  }

  return (
    <>
      <Card sx={{ p: 3, maxWidth: 480 }}>
        <Typography variant="h6" gutterBottom>{t('settings.title')}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('settings.description')}
        </Typography>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            type="number"
            label={t('settings.timeoutSeconds')}
            helperText={t('settings.timeoutSecondsHelp')}
            value={config.timeout_seconds}
            onChange={(e) => handleChange('timeout_seconds', Number(e.target.value))}
            disabled={saving}
            size="small"
            slotProps={{ htmlInput: { min: 1, max: 60 } }}
          />
          <TextField
            label={t('settings.proxyUrl')}
            helperText={t('settings.proxyUrlHelp')}
            value={config.proxy_url || ''}
            onChange={(e) => handleChange('proxy_url', e.target.value)}
            disabled={saving}
            size="small"
          />
        </Box>
      </Card>

      <AppSnackbar
        open={notification.open}
        message={notification.message}
        severity={notification.severity}
        onClose={hideNotification}
      />

      {saving && (
        <Box sx={{ position: 'fixed', bottom: 16, right: 16, zIndex: 2000 }}>
          <CircularProgress size={24} />
        </Box>
      )}
    </>
  );
}
