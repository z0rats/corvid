import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useQuota } from '../../../hooks/api/useQuota';

function QuotaRow({ quota }) {
  const { t } = useTranslation('settings');

  if (!quota.configured) {
    return (
      <Box sx={{ py: 1 }}>
        <Typography variant="body2" fontWeight={600}>{quota.provider}</Typography>
        <Typography variant="caption" color="text.secondary">{t('quota.notConfigured')}</Typography>
      </Box>
    );
  }

  if (quota.error) {
    return (
      <Box sx={{ py: 1 }}>
        <Typography variant="body2" fontWeight={600}>{quota.provider}</Typography>
        <Typography variant="caption" color="error.main">{quota.error}</Typography>
      </Box>
    );
  }

  const hasUsedLimit = quota.used !== null && quota.used !== undefined && quota.limit !== null && quota.limit !== undefined;
  const percentUsed = hasUsedLimit && quota.limit > 0 ? Math.min(100, (quota.used / quota.limit) * 100) : null;

  return (
    <Box sx={{ py: 1 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="baseline">
        <Typography variant="body2" fontWeight={600}>{quota.provider}</Typography>
        <Typography variant="caption" color="text.secondary">
          {hasUsedLimit
            ? t('quota.usedOfLimit', { used: quota.used, limit: quota.limit })
            : t('quota.remainingOnly', { remaining: quota.remaining })}
        </Typography>
      </Stack>
      {percentUsed !== null && (
        <LinearProgress variant="determinate" value={percentUsed} sx={{ mt: 0.5, borderRadius: 1 }} />
      )}
    </Box>
  );
}

export default function QuotaPanel() {
  const { t } = useTranslation('settings');
  const { quotas, loading, error, refreshQuota } = useQuota();

  useEffect(() => {
    refreshQuota();
  }, [refreshQuota]);

  return (
    <Paper elevation={0} sx={{ p: 2, mb: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Typography variant="subtitle1" fontWeight={600}>{t('quota.title')}</Typography>
        <Button
          size="small"
          startIcon={loading ? <CircularProgress size={14} /> : <RefreshIcon fontSize="small" />}
          onClick={refreshQuota}
          disabled={loading}
        >
          {t('quota.refresh')}
        </Button>
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t('quota.description')}
      </Typography>

      {error ? (
        <Typography variant="body2" color="error.main">{error}</Typography>
      ) : (
        <Stack divider={<Box sx={{ borderBottom: 1, borderColor: 'divider' }} />}>
          {quotas.map((quota) => (
            <QuotaRow key={quota.provider} quota={quota} />
          ))}
        </Stack>
      )}
    </Paper>
  );
}
