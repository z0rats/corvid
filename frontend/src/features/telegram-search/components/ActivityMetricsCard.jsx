import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import { formatCompact, formatDate, formatPercent } from '../utils/telegramFormat';

function Stat({ label, value, hint }) {
  return (
    <Box sx={{ minWidth: 120 }}>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>{label}</Typography>
      <Typography variant="h6" component="p">{value ?? '-'}</Typography>
      {hint && <Typography variant="caption" color="text.secondary">{hint}</Typography>}
    </Box>
  );
}

export default function ActivityMetricsCard({ metrics }) {
  const { t } = useTranslation('telegramSearch');

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle1" component="h2" sx={{ mb: 0.5 }}>{t('activity.title')}</Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5 }}>
        {t('activity.basis', {
          count: metrics.posts_sampled,
          from: formatDate(metrics.first_sampled_at) ?? '-',
          to: formatDate(metrics.last_post_at) ?? '-',
        })}
      </Typography>
      <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 3 }}>
        <Stat label={t('activity.lastPost')} value={formatDate(metrics.last_post_at)} />
        <Stat label={t('activity.postsPerDay')} value={metrics.posts_per_day} />
        <Stat
          label={t('activity.avgViews')}
          value={formatCompact(metrics.avg_views)}
          hint={metrics.median_views != null ? t('activity.medianViews', { value: formatCompact(metrics.median_views) }) : null}
        />
        <Stat
          label={t('activity.viewsToMembers')}
          value={formatPercent(metrics.views_to_members)}
          hint={t('activity.viewsToMembersHint')}
        />
        <Stat
          label={t('activity.forwarded')}
          value={formatPercent(metrics.forwarded_ratio)}
          hint={t('activity.forwardedCount', { count: metrics.forwarded_count })}
        />
        <Stat label={t('activity.media')} value={formatPercent(metrics.media_ratio)} />
      </Stack>
    </Paper>
  );
}
