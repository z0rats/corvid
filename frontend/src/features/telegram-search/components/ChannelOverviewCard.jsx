import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import OpenInNewIcon from '@mui/icons-material/OpenInNewOutlined';
import VerifiedIcon from '@mui/icons-material/Verified';

import { formatDate } from '../utils/telegramFormat';

function Fact({ label, value }) {
  if (value == null || value === '') return null;
  return (
    <Box>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>{label}</Typography>
      <Typography variant="body2">{value}</Typography>
    </Box>
  );
}

export default function ChannelOverviewCard({ profile }) {
  const { t } = useTranslation('telegramSearch');
  const counters = Object.entries(profile.media_counters || {});

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap', mb: 1 }}>
        <Typography variant="h6" component="h2">{profile.title}</Typography>
        {profile.verified && <VerifiedIcon color="primary" fontSize="small" titleAccess={t('overview.verified')} />}
        <Chip size="small" label={t(`overview.kind.${profile.kind}`)} />
        <Link
          href={profile.url}
          target="_blank"
          rel="noopener noreferrer"
          sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
        >
          @{profile.username} <OpenInNewIcon fontSize="inherit" />
        </Link>
      </Stack>

      {profile.description && (
        <Typography variant="body2" sx={{ whiteSpace: 'pre-line', mb: 1.5 }}>
          {profile.description}
        </Typography>
      )}

      <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 3 }}>
        <Fact
          label={profile.kind === 'group' ? t('overview.members') : t('overview.subscribers')}
          value={profile.member_count?.toLocaleString()}
        />
        <Fact label={t('overview.online')} value={profile.online_count?.toLocaleString()} />
        <Fact label={t('overview.created')} value={formatDate(profile.created_at)} />
        {counters.map(([name, count]) => (
          <Fact key={name} label={t('overview.counter', { name })} value={count.toLocaleString()} />
        ))}
        {profile.photo_url && (
          // A link, not an <img>: embedding would fetch from Telegram's CDN on every view.
          <Fact
            label={t('overview.photo')}
            value={<Link href={profile.photo_url} target="_blank" rel="noopener noreferrer">{t('overview.openPhoto')}</Link>}
          />
        )}
      </Stack>

      {!profile.preview_available && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {t(profile.kind === 'group' ? 'overview.noPreviewGroup' : 'overview.noPreview')}
        </Alert>
      )}
    </Paper>
  );
}
