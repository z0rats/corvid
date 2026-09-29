import { useTranslation } from 'react-i18next';
import Avatar from '@mui/material/Avatar';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import { formatEpoch, formatLocation } from '../utils/steamFormat';

function Stat({ label, value }) {
  return (
    <Stack sx={{ minWidth: 120 }}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body1">{value}</Typography>
    </Stack>
  );
}

function BanChips({ bans }) {
  const { t } = useTranslation('steamRecon');
  const chips = [];
  if (bans.vac_banned || bans.number_of_vac_bans > 0) {
    chips.push(t('profile.bans.vac', { count: bans.number_of_vac_bans }));
  }
  if (bans.number_of_game_bans > 0) {
    chips.push(t('profile.bans.game', { count: bans.number_of_game_bans }));
  }
  if (bans.community_banned) chips.push(t('profile.bans.community'));
  if (bans.economy_ban && bans.economy_ban !== 'none') {
    chips.push(t('profile.bans.economy', { state: bans.economy_ban }));
  }

  if (chips.length === 0) {
    return <Chip size="small" color="success" variant="outlined" label={t('profile.bans.none')} />;
  }
  const hasBan = bans.number_of_vac_bans > 0 || bans.number_of_game_bans > 0;
  return (
    <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
      {chips.map((label) => (
        <Chip key={label} size="small" color="error" label={label} />
      ))}
      {hasBan && (
        <Typography variant="caption" color="text.secondary">
          {t('profile.bans.daysSince', { count: bans.days_since_last_ban })}
        </Typography>
      )}
    </Stack>
  );
}

export default function ProfileCard({ result }) {
  const { t } = useTranslation('steamRecon');
  const { profile, quick_links: quickLinks } = result;
  const unknown = t('profile.unknown');

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ alignItems: 'flex-start' }}>
        <Avatar
          src={profile.avatar_url || undefined}
          alt={profile.persona_name || ''}
          variant="rounded"
          sx={{ width: 96, height: 96 }}
        />
        <Stack spacing={0.5} sx={{ flexGrow: 1, minWidth: 0 }}>
          <Typography variant="h6" component="h2" noWrap>
            {profile.persona_name || t('profile.unnamed')}
          </Typography>
          {profile.real_name && (
            <Typography variant="body2" color="text.secondary">
              {profile.real_name}
            </Typography>
          )}
          <Typography variant="body2" color="text.secondary">
            {t('profile.steamId')}: {profile.steamid64}
          </Typography>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
            <Chip size="small" variant="outlined" label={t(`profile.visibility.${profile.visibility}`)} />
            {profile.profile_url && (
              <Link href={profile.profile_url} target="_blank" rel="noopener noreferrer" variant="body2">
                {t('profile.openOnSteam')}
              </Link>
            )}
          </Stack>
        </Stack>
      </Stack>

      <Divider sx={{ my: 2 }} />

      <Stack direction="row" useFlexGap spacing={3} sx={{ flexWrap: 'wrap', mb: 2 }}>
        <Stat label={t('profile.level')} value={profile.level ?? unknown} />
        <Stat
          label={t('profile.games')}
          value={profile.game_count ?? t('profile.gamesPrivate')}
        />
        <Stat label={t('profile.created')} value={formatEpoch(profile.created_at) ?? unknown} />
        <Stat label={t('profile.lastLogoff')} value={formatEpoch(profile.last_logoff) ?? unknown} />
        <Stat label={t('profile.location')} value={formatLocation(profile.location) ?? unknown} />
      </Stack>

      {profile.bans && (
        <Stack spacing={0.5} sx={{ mb: 2 }}>
          <Typography variant="caption" color="text.secondary">
            {t('profile.bans.title')}
          </Typography>
          <BanChips bans={profile.bans} />
        </Stack>
      )}

      <Typography variant="caption" color="text.secondary">
        {t('profile.quickLinks')}
      </Typography>
      <Stack direction="row" useFlexGap spacing={1} sx={{ flexWrap: 'wrap', mt: 0.5 }}>
        {quickLinks.map((link) => (
          <Button
            key={link.id}
            size="small"
            variant="outlined"
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {link.label}
          </Button>
        ))}
      </Stack>
    </Paper>
  );
}
