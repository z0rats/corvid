import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import LinearProgress from '@mui/material/LinearProgress';
import Link from '@mui/material/Link';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import { useGhuntProfile } from '../hooks/api/useGhuntProfile';

function DetailRow({ label, value }) {
  if (!value) return null;
  return (
    <Box sx={{ display: 'flex', gap: 1 }}>
      <Typography variant="body2" color="text.secondary" sx={{ minWidth: 140 }}>{label}</Typography>
      <Typography variant="body2">{value}</Typography>
    </Box>
  );
}

export default function GhuntProfilePanel() {
  const { t } = useTranslation('emailSearch');
  const [email, setEmail] = useState('');
  const { health, result, loading, error, lookup, reset } = useGhuntProfile();

  const sessionConfigured = health?.session_configured === true;

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = email.trim();
    if (!trimmed) return;
    reset();
    lookup(trimmed);
  };

  const errorMessage = error
    ? t(`ghunt.errors.${error.code}`, { defaultValue: error.message })
    : null;

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" sx={{ mb: 1 }}>{t('ghunt.title')}</Typography>
      <Alert severity="warning" variant="outlined" sx={{ mb: 2, borderRadius: 1 }}>
        {t('ghunt.consentDescription')}{' '}
        <Link href="https://github.com/mxrch/GHunt" target="_blank" rel="noopener noreferrer">
          {t('ghunt.methodLink')}
        </Link>
      </Alert>

      {health && !sessionConfigured && (
        <Alert severity="info" sx={{ mb: 2 }}>{t('ghunt.noSessionConfigured')}</Alert>
      )}

      <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <TextField
          fullWidth
          size="small"
          label={t('ghunt.emailLabel')}
          placeholder={t('ghunt.emailPlaceholder')}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={!sessionConfigured || loading}
        />
        <Button
          type="submit"
          variant="outlined"
          startIcon={<TravelExploreIcon />}
          disabled={!sessionConfigured || !email.trim() || loading}
          sx={{ whiteSpace: 'nowrap' }}
        >
          {t('ghunt.lookupButton')}
        </Button>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {errorMessage && <Alert severity="error" sx={{ mb: 2 }}>{errorMessage}</Alert>}

      {result && (
        <Stack spacing={1.5}>
          <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
            {result.profile_photo?.url && (
              <Avatar src={result.profile_photo.url} sx={{ width: 56, height: 56 }} />
            )}
            <Box>
              <Typography variant="body1" sx={{ fontWeight: 'medium' }}>{result.email}</Typography>
              <Typography variant="caption" color="text.secondary">
                {t('ghunt.gaiaId')}: {result.gaia_id}
              </Typography>
            </Box>
          </Stack>

          <Divider />

          <DetailRow
            label={t('ghunt.profilePhoto')}
            value={result.profile_photo
              ? result.profile_photo.is_default ? t('ghunt.defaultPhoto') : result.profile_photo.url
              : null}
          />
          <DetailRow
            label={t('ghunt.coverPhoto')}
            value={result.cover_photo
              ? result.cover_photo.is_default ? t('ghunt.defaultPhoto') : result.cover_photo.url
              : null}
          />
          <DetailRow label={t('ghunt.lastProfileEdit')} value={result.last_profile_edit} />

          {result.user_types.length > 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                {t('ghunt.userTypes')}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {result.user_types.map((type) => <Chip key={type} label={type} size="small" />)}
              </Box>
            </Box>
          )}

          {result.activated_services.length > 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                {t('ghunt.activatedServices')}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {result.activated_services.map((app) => <Chip key={app} label={app} size="small" />)}
              </Box>
            </Box>
          )}

          {(result.play_games || result.maps || result.calendar) && (
            <Box component="details">
              <Typography component="summary" variant="body2" color="text.secondary" sx={{ cursor: 'pointer' }}>
                {t('ghunt.rawDataToggle')}
              </Typography>
              <Box
                component="pre"
                sx={{
                  mt: 1,
                  p: 1.5,
                  borderRadius: 1,
                  bgcolor: 'action.hover',
                  fontSize: '0.75rem',
                  overflow: 'auto',
                  maxHeight: 300,
                }}
              >
                {JSON.stringify(
                  { play_games: result.play_games, maps: result.maps, calendar: result.calendar },
                  null,
                  2
                )}
              </Box>
            </Box>
          )}

          <Button size="small" onClick={() => { reset(); setEmail(''); }} sx={{ alignSelf: 'flex-start' }}>
            {t('ghunt.recheckButton')}
          </Button>
        </Stack>
      )}
    </Box>
  );
}
