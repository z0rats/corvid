import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import LinearProgress from '@mui/material/LinearProgress';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

const STATUS_COLORS = {
  ok: 'success',
  rejected: 'error',
  rate_limited: 'warning',
  plan_required: 'warning',
  unreachable: 'warning',
  error: 'error',
  not_configured: 'default',
  untestable: 'default',
};

const isNumber = (value) => typeof value === 'number';

function QuotaLine({ quota }) {
  const { t } = useTranslation('settings');
  if (!quota) return null;
  const hasUsedLimit = isNumber(quota.used) && isNumber(quota.limit);
  if (!hasUsedLimit && !isNumber(quota.remaining)) return null;
  const percentUsed = hasUsedLimit && quota.limit > 0 ? Math.min(100, (quota.used / quota.limit) * 100) : null;

  return (
    <Box sx={{ mt: 0.5 }}>
      <Typography variant="caption" color="text.secondary">
        {hasUsedLimit
          ? t('keyTest.usedOfLimit', { used: quota.used, limit: quota.limit })
          : t('keyTest.remainingOnly', { remaining: quota.remaining })}
        {quota.period ? ` (${t(`keyTest.periods.${quota.period}`, { defaultValue: quota.period })})` : ''}
      </Typography>
      {percentUsed !== null && (
        <LinearProgress
          variant="determinate"
          value={percentUsed}
          aria-label={t('keyTest.quotaUsed')}
          sx={{ mt: 0.5, borderRadius: 1 }}
        />
      )}
    </Box>
  );
}

/**
 * Test button plus the last live result for one service. A service that can't be tested
 * without spending quota (or acting on an account) says why instead of offering a button.
 */
export default function KeyTestStatus({ exemptReason, result, testing, onTest }) {
  const { t } = useTranslation('settings');

  if (exemptReason) {
    return (
      <Typography variant="caption" color="text.secondary">
        {t('keyTest.untestable', { reason: exemptReason })}
      </Typography>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Button
          size="small"
          variant="outlined"
          onClick={onTest}
          disabled={testing}
          startIcon={testing ? <CircularProgress size={14} /> : undefined}
        >
          {t('keyTest.test')}
        </Button>
        {result && !testing && (
          <Tooltip title={result.http_status ? `${result.detail} (HTTP ${result.http_status})` : result.detail}>
            <Chip
              size="small"
              color={STATUS_COLORS[result.status] ?? 'default'}
              label={t(`keyTest.statuses.${result.status}`, { defaultValue: result.status })}
            />
          </Tooltip>
        )}
      </Box>
      {result && !testing && result.status !== 'ok' && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
          {result.detail}
        </Typography>
      )}
      {result && !testing && <QuotaLine quota={result.quota} />}
    </Box>
  );
}
