import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import { buildPrefillUrl } from '../../../core/utils/crossFeatureNav';
import { TELEGRAM_SCAN_PATH } from '../utils/telegramSearchConfig';

function Section({ title, hint, children }) {
  return (
    <Box sx={{ mb: 1.5 }}>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
        {title}{hint ? ` — ${hint}` : ''}
      </Typography>
      <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 0.75 }}>{children}</Stack>
    </Box>
  );
}

/** Channels this one reposts and promotes - each linked one opens its own scan. */
export default function ChannelNetworkCard({ metrics, disabled }) {
  const { t } = useTranslation('telegramSearch');
  const navigate = useNavigate();
  const sources = metrics.top_forward_sources || [];
  const mentions = metrics.top_mentions || [];
  if (sources.length === 0 && mentions.length === 0) return null;

  const scanChip = (username, label) => (
    <Chip
      key={`${username}-${label}`}
      size="small"
      variant="outlined"
      color="primary"
      label={label}
      disabled={disabled}
      onClick={() => navigate(buildPrefillUrl(TELEGRAM_SCAN_PATH, username))}
    />
  );

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle1" component="h2" sx={{ mb: 1 }}>{t('network.title')}</Typography>

      {sources.length > 0 && (
        <Section title={t('network.forwardSources')} hint={t('network.clickToScan')}>
          {sources.map((source) => {
            const label = `${source.name || t('network.hiddenSender')} (${source.count})`;
            if (source.username) return scanChip(source.username, `${label} @${source.username}`);
            return (
              <Chip
                key={`${source.name}-hidden`}
                size="small"
                label={label}
                title={t(source.name ? 'network.privateSource' : 'network.hiddenSenderHint')}
              />
            );
          })}
        </Section>
      )}

      {mentions.length > 0 && (
        <Section title={t('network.mentions')} hint={t('network.clickToScan')}>
          {mentions.map(({ username, count }) => scanChip(username, `@${username} (${count})`))}
        </Section>
      )}
    </Paper>
  );
}
