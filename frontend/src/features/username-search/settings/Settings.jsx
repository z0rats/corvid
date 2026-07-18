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

import { useUsernameSearchSettings } from '../hooks/api/useUsernameSearchSettings';
import { useSocialAnalyzerSettings } from '../hooks/api/useSocialAnalyzerSettings';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import AppSnackbar from '../../../core/components/ui/AppSnackbar';
import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('UsernameSearchSettings');

export default function Settings() {
  const { t } = useTranslation('usernameSearch');
  const { config, loading, saving, updateConfig, setConfig } = useUsernameSearchSettings();
  const {
    config: saConfig,
    loading: saLoading,
    saving: saSaving,
    updateConfig: updateSaConfig,
    setConfig: setSaConfig,
  } = useSocialAnalyzerSettings();
  const { notification, showSuccess, showError, hideNotification } = useNotification();
  const [refreshing, setRefreshing] = useState(false);
  const [checkingUpdate, setCheckingUpdate] = useState(false);
  const [checkingMaigretUpdate, setCheckingMaigretUpdate] = useState(false);

  const handleError = useCallback((error) => {
    logger.error('Settings error:', error);
    showError(error.response?.data?.detail || error.message || t('settings.updateError'));
  }, [showError, t]);

  const handleSaChange = useCallback(async (field, value) => {
    const result = await updateSaConfig({ [field]: value });
    if (result.success) {
      showSuccess(t('settings.updateSuccess'));
    } else {
      handleError(result.error);
    }
  }, [updateSaConfig, showSuccess, handleError, t]);

  const handleCheckUpdate = useCallback(async () => {
    setCheckingUpdate(true);
    try {
      const info = await usernameSearchApi.checkSocialAnalyzerUpdate();
      setSaConfig((prev) => ({
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
  }, [setSaConfig, showSuccess, handleError, t]);

  const handleCheckMaigretUpdate = useCallback(async () => {
    setCheckingMaigretUpdate(true);
    try {
      const info = await usernameSearchApi.checkMaigretUpdate();
      setConfig((prev) => ({
        ...prev,
        latest_pypi_version: info.latest_version,
        pypi_checked_at: new Date().toISOString(),
      }));
      showSuccess(t('settings.pypiCheckSuccess'));
    } catch (err) {
      handleError(err);
    } finally {
      setCheckingMaigretUpdate(false);
    }
  }, [setConfig, showSuccess, handleError, t]);

  const handleChange = useCallback(async (field, value) => {
    const result = await updateConfig({ [field]: value });
    if (result.success) {
      showSuccess(t('settings.updateSuccess'));
    } else {
      handleError(result.error);
    }
  }, [updateConfig, showSuccess, handleError, t]);

  const handleRefreshNow = useCallback(async () => {
    setRefreshing(true);
    try {
      await usernameSearchApi.refreshDb();
      showSuccess(t('settings.dbRefreshSuccess'));
    } catch (err) {
      handleError(err);
    } finally {
      setRefreshing(false);
    }
  }, [showSuccess, handleError, t]);

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
            slotProps={{ htmlInput: { min: 1, max: 120 } }}
          />
          <TextField
            type="number"
            label={t('settings.maxConcurrency')}
            helperText={t('settings.maxConcurrencyHelp')}
            value={config.max_concurrency}
            onChange={(e) => handleChange('max_concurrency', Number(e.target.value))}
            disabled={saving}
            size="small"
            slotProps={{ htmlInput: { min: 1, max: 500 } }}
          />
          <TextField
            type="number"
            label={t('settings.topSitesCount')}
            helperText={t('settings.topSitesCountHelp')}
            value={config.top_sites_count}
            onChange={(e) => handleChange('top_sites_count', Number(e.target.value))}
            disabled={saving}
            size="small"
            slotProps={{ htmlInput: { min: 0, max: 10000 } }}
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

        <Typography variant="subtitle1" gutterBottom>{t('settings.dbUpdateSection')}</Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ flex: 1, mr: 2 }}>
            {t('settings.autoUpdateDbDescription')}
          </Typography>
          <Switch
            checked={config.auto_update_db_enabled}
            onChange={(e) => handleChange('auto_update_db_enabled', e.target.checked)}
            disabled={saving}
            color="primary"
          />
        </Box>

        {config.auto_update_db_enabled && (
          <TextField
            type="number"
            label={t('settings.autoUpdateIntervalHours')}
            value={config.auto_update_interval_hours}
            onChange={(e) => handleChange('auto_update_interval_hours', Number(e.target.value))}
            disabled={saving}
            size="small"
            fullWidth
            sx={{ mb: 2 }}
            slotProps={{ htmlInput: { min: 1, max: 168 } }}
          />
        )}

        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {config.db_last_updated_at
            ? t('settings.dbStatusUpdated', { count: config.db_site_count, date: new Date(config.db_last_updated_at).toLocaleString() })
            : t('settings.dbStatusBundled', { count: config.db_site_count })}
        </Typography>

        <Button
          variant="outlined"
          size="small"
          startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
          onClick={handleRefreshNow}
          disabled={refreshing}
        >
          {t('settings.refreshDbNow')}
        </Button>

        <Divider sx={{ my: 3 }} />

        <Typography variant="subtitle1" gutterBottom>{t('settings.maigretVersionSection')}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {config.latest_pypi_version
            ? t('settings.saVersionStatus', {
                latest: config.latest_pypi_version,
                date: config.pypi_checked_at ? new Date(config.pypi_checked_at).toLocaleString() : '',
              })
            : t('settings.saVersionNeverChecked')}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
          {t('settings.maigretUpdateRequiresRebuild')}
        </Typography>

        <Button
          variant="outlined"
          size="small"
          startIcon={checkingMaigretUpdate ? <CircularProgress size={16} /> : <RefreshIcon />}
          onClick={handleCheckMaigretUpdate}
          disabled={checkingMaigretUpdate}
        >
          {t('settings.saCheckUpdate')}
        </Button>
      </Card>

      <Card sx={{ p: 3, maxWidth: 480, mt: 3 }}>
        <Typography variant="h6" gutterBottom>{t('settings.saTitle')}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('settings.saDescription')}
        </Typography>

        <Divider sx={{ my: 2 }} />

        {saLoading ? (
          <Skeleton variant="rectangular" height={100} />
        ) : (
          <>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                type="number"
                label={t('settings.saTimeoutSeconds')}
                helperText={t('settings.saTimeoutSecondsHelp')}
                value={saConfig.timeout_seconds}
                onChange={(e) => handleSaChange('timeout_seconds', Number(e.target.value))}
                disabled={saSaving}
                size="small"
                slotProps={{ htmlInput: { min: 0, max: 120 } }}
              />
              <TextField
                type="number"
                label={t('settings.topSitesCount')}
                helperText={t('settings.topSitesCountHelp')}
                value={saConfig.top_sites_count}
                onChange={(e) => handleSaChange('top_sites_count', Number(e.target.value))}
                disabled={saSaving}
                size="small"
                slotProps={{ htmlInput: { min: 0 } }}
              />
            </Box>

            <Divider sx={{ my: 3 }} />

            <Typography variant="subtitle1" gutterBottom>{t('settings.saVersionSection')}</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {saConfig.latest_pypi_version
                ? t('settings.saVersionStatus', {
                    latest: saConfig.latest_pypi_version,
                    date: saConfig.pypi_checked_at ? new Date(saConfig.pypi_checked_at).toLocaleString() : '',
                  })
                : t('settings.saVersionNeverChecked')}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
              {t('settings.saUpdateRequiresRebuild')}
            </Typography>

            <Button
              variant="outlined"
              size="small"
              startIcon={checkingUpdate ? <CircularProgress size={16} /> : <RefreshIcon />}
              onClick={handleCheckUpdate}
              disabled={checkingUpdate}
            >
              {t('settings.saCheckUpdate')}
            </Button>
          </>
        )}
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
