import { useCallback } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import Skeleton from '@mui/material/Skeleton';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import { useRuBusinessCheckSettings } from '../hooks/api/useRuBusinessCheckSettings';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import AppSnackbar from '../../../core/components/ui/AppSnackbar';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('RuBusinessCheckSettings');

export default function Settings() {
  const { config, loading, saving, updateConfig } = useRuBusinessCheckSettings();
  const { notification, showSuccess, showError, hideNotification } = useNotification();

  const handleChange = useCallback(async (field, value) => {
    const result = await updateConfig({ [field]: value });
    if (result.success) {
      showSuccess('Настройки сохранены');
    } else {
      logger.error('Settings error:', result.error);
      showError(result.error?.response?.data?.detail || result.error?.message || 'Не удалось сохранить настройки');
    }
  }, [updateConfig, showSuccess, showError]);

  if (loading) {
    return (
      <Card sx={{ p: 3 }}>
        <Skeleton variant="rectangular" height={150} />
      </Card>
    );
  }

  return (
    <>
      <Card sx={{ p: 3, maxWidth: 480 }}>
        <Typography variant="h6" gutterBottom>Настройки RU Business Check</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Пороги движка флагов и срок хранения истории проверок.
        </Typography>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            type="number"
            label="Порог «свежей регистрации», дней"
            helperText="Ниже этого возраста регистрации срабатывает мягкий флаг"
            value={config.fresh_registration_threshold_days}
            onChange={(e) => handleChange('fresh_registration_threshold_days', Number(e.target.value))}
            disabled={saving}
            size="small"
            slotProps={{ htmlInput: { min: 1, max: 3650 } }}
          />
          <TextField
            type="number"
            label="Хранение истории, дней"
            helperText="0 = хранить бессрочно. Включает сырые данные источников"
            value={config.history_retention_days}
            onChange={(e) => handleChange('history_retention_days', Number(e.target.value))}
            disabled={saving}
            size="small"
            slotProps={{ htmlInput: { min: 0, max: 3650 } }}
          />
        </Box>

        <Divider sx={{ my: 3 }} />

        <Typography variant="subtitle1" gutterBottom>Арбитраж</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            type="number"
            label="Порог «небольшого» иска, ₽"
            helperText="Единичное разрешённое дело как ответчик ниже этой суммы — мягкий флаг"
            value={config.small_claim_amount_threshold}
            onChange={(e) => handleChange('small_claim_amount_threshold', Number(e.target.value))}
            disabled={saving}
            size="small"
            slotProps={{ htmlInput: { min: 0 } }}
          />
          <TextField
            type="number"
            label="Порог «крупного» иска, ₽"
            helperText="Любое дело как ответчик на сумму от этого порога — мягкий флаг"
            value={config.large_claim_amount_threshold}
            onChange={(e) => handleChange('large_claim_amount_threshold', Number(e.target.value))}
            disabled={saving}
            size="small"
            slotProps={{ htmlInput: { min: 0 } }}
          />
          <TextField
            type="number"
            label="Порог количества дел как ответчик"
            helperText="От этого числа дел как ответчик — мягкий флаг, независимо от суммы"
            value={config.multiple_claims_defendant_threshold}
            onChange={(e) => handleChange('multiple_claims_defendant_threshold', Number(e.target.value))}
            disabled={saving}
            size="small"
            slotProps={{ htmlInput: { min: 1, max: 100 } }}
          />
        </Box>

        <Divider sx={{ my: 3 }} />

        <Typography variant="subtitle1" gutterBottom>Прозрачный бизнес</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            type="number"
            label="Порог «массового адреса», компаний"
            helperText="От этого числа других компаний по тому же адресу — мягкий флаг"
            value={config.mass_address_threshold}
            onChange={(e) => handleChange('mass_address_threshold', Number(e.target.value))}
            disabled={saving}
            size="small"
            slotProps={{ htmlInput: { min: 1, max: 1000 } }}
          />
        </Box>

        <Divider sx={{ my: 3 }} />

        <Typography variant="subtitle1" gutterBottom>Возраст домена</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            type="number"
            label="Порог разрыва «домен моложе компании», дней"
            helperText="От этого разрыва между регистрацией компании и появлением домена — мягкий флаг"
            value={config.domain_age_mismatch_threshold_days}
            onChange={(e) => handleChange('domain_age_mismatch_threshold_days', Number(e.target.value))}
            disabled={saving}
            size="small"
            slotProps={{ htmlInput: { min: 1, max: 3650 } }}
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
