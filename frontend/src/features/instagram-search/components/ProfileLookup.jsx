import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Grow from '@mui/material/Grow';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import OpenInNewIcon from '@mui/icons-material/OpenInNewOutlined';

import ProfileOverviewCard from './ui/ProfileOverviewCard';
import SessionModeBanner from './ui/SessionModeBanner';
import WelcomeScreen from './ui/WelcomeScreen';
import { useInstagramSearch } from '../hooks/ui/useInstagramSearch';

export default function ProfileLookup() {
  const { t } = useTranslation('instagramSearch');
  const { username, setUsername, result, loading, error, lookupProfile } = useInstagramSearch();

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      lookupProfile();
    }
  };

  return (
    <>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField
            fullWidth
            size="small"
            label={t('form.usernameLabel')}
            placeholder={t('form.usernamePlaceholder')}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <Box>
            <Button
              variant="contained"
              onClick={() => lookupProfile()}
              disabled={loading || !username.trim()}
              sx={{ whiteSpace: 'nowrap' }}
            >
              {loading ? <CircularProgress size={20} /> : t('form.lookupButton')}
            </Button>
          </Box>
        </Stack>
        <Link
          href="https://z0rats.github.io/corvid/features/instagram-search/"
          target="_blank"
          rel="noopener noreferrer"
          variant="caption"
          color="text.secondary"
          sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, mt: 1.5 }}
        >
          {t('docs.viewDocs')} <OpenInNewIcon fontSize="inherit" />
        </Link>
      </Paper>

      {error && (
        <Grow in={true}>
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        </Grow>
      )}

      {result ? (
        <>
          <SessionModeBanner mode={result.mode} />
          <ProfileOverviewCard result={result} />
        </>
      ) : (
        !loading && <WelcomeScreen />
      )}
    </>
  );
}
