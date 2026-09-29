import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Grow from '@mui/material/Grow';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';

import ApiKeyRequiredAlert from './ApiKeyRequiredAlert';
import ProfileCard from './ProfileCard';
import WelcomeScreen from './WelcomeScreen';
import { useSteamProfile } from '../hooks/useSteamProfile';

export default function ProfileLookup() {
  const { t } = useTranslation('steamRecon');
  const { target, setTarget, result, loading, error, errorCode, lookupProfile } = useSteamProfile();

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
            label={t('form.targetLabel')}
            placeholder={t('form.targetPlaceholder')}
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <Box>
            <Button
              variant="contained"
              onClick={() => lookupProfile()}
              disabled={loading || !target.trim()}
              sx={{ whiteSpace: 'nowrap' }}
            >
              {loading ? <CircularProgress size={20} /> : t('form.lookupButton')}
            </Button>
          </Box>
        </Stack>
      </Paper>

      {errorCode === 'STEAM_NOT_CONFIGURED' && <ApiKeyRequiredAlert />}

      {error && errorCode !== 'STEAM_NOT_CONFIGURED' && (
        <Grow in={true}>
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        </Grow>
      )}

      {result ? <ProfileCard result={result} /> : !loading && !error && <WelcomeScreen />}
    </>
  );
}
