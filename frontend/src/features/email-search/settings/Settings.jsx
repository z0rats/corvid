import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import Skeleton from '@mui/material/Skeleton';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import RefreshIcon from '@mui/icons-material/Refresh';

import { useEmailSearchSettings } from '../hooks/api/useEmailSearchSettings';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import AppSnackbar from '../../../core/components/ui/AppSnackbar';
import { emailSearchApi } from '../services/api/emailSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('EmailSearchSettings');

export default function Settings() {
  const { t } = useTranslation('emailSearch');
  const { config, loading, saving, updateConfig, setConfig } = useEmailSearchSettings();
  const { notification, showSuccess, showError, hideNotification } = useNotification();
  const [checkingUpdate, setCheckingUpdate] = useState(false);

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

  const handleCheckUpdate = useCallback(async () => {
    setCheckingUpdate(true);
    try {
      const info = await emailSearchApi.checkUpdate();
      setConfig((prev) => ({
        ...prev,
        latest_pypi_version: info.latest_version,
        pypi_checked_at: new Date().toISOString(),
      }));
      showSuccess(t('settings.pypiCheckSuccess'));
    } catch (err) {
      handleError(err);
    } finally {
      setCheckingUpdate(false);
    }
  }, [setConfig, showSuccess, handleError, t]);

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
            type="number"
            label={t('settings.maxConcurrency')}
            helperText={t('settings.maxConcurrencyHelp')}
            value={config.max_concurrency}
            onChange={(e) => handleChange('max_concurrency', Number(e.target.value))}
            disabled={saving}
            size="small"
            slotProps={{ htmlInput: { min: 1, max: 50 } }}
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

        <Divider sx={{ my: 3 }} />

        <Typography variant="subtitle1" gutterBottom>{t('settings.optionalCheckersSection')}</Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ flex: 1, mr: 2 }}>
            {t('settings.useTorDescription')}
          </Typography>
          <Switch
            checked={config.use_tor}
            onChange={(e) => handleChange('use_tor', e.target.checked)}
            disabled={saving}
            color="primary"
          />
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ flex: 1, mr: 2 }}>
            {t('settings.enableSmtpChecksDescription')}
          </Typography>
          <Switch
            checked={config.enable_smtp_checks}
            onChange={(e) => handleChange('enable_smtp_checks', e.target.checked)}
            disabled={saving}
            color="primary"
          />
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ flex: 1, mr: 2 }}>
            {t('settings.enableHeadlessChecksDescription')}
          </Typography>
          <Switch
            checked={config.enable_headless_checks}
            onChange={(e) => handleChange('enable_headless_checks', e.target.checked)}
            disabled={saving}
            color="primary"
          />
        </Box>

        <Divider sx={{ my: 3 }} />

        <Typography variant="subtitle1" gutterBottom>{t('settings.versionSection')}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {config.latest_pypi_version
            ? t('settings.versionStatus', {
                latest: config.latest_pypi_version,
                date: config.pypi_checked_at ? new Date(config.pypi_checked_at).toLocaleString() : '',
              })
            : t('settings.versionNeverChecked')}
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
          {t('settings.updateRequiresRebuild')}
        </Typography>

        <Button
          variant="outlined"
          size="small"
          startIcon={checkingUpdate ? <CircularProgress size={16} /> : <RefreshIcon />}
          onClick={handleCheckUpdate}
          disabled={checkingUpdate}
        >
          {t('settings.checkUpdate')}
        </Button>
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
