import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import api from '../../services/baseApi';
import { usePersistentState } from '../../hooks/ui/usePersistentState';

/**
 * First-run hint on the start screen: shown only while no API key at all is configured, saying
 * what already works keyless and which (free-tier) keys are worth adding first. Dismissible.
 */
export default function ApiKeysOnboardingHint() {
  const { t } = useTranslation('commandPalette');
  const [dismissed, setDismissed] = usePersistentState('onboarding.apiKeysHintDismissed', false);
  const [noKeys, setNoKeys] = useState(false);

  useEffect(() => {
    if (dismissed) return undefined;
    let ignore = false;
    api.get('/api/apikeys/configured')
      .then((response) => {
        if (!ignore) setNoKeys(!Object.values(response.data ?? {}).some(Boolean));
      })
      .catch(() => {});
    return () => { ignore = true; };
  }, [dismissed]);

  if (dismissed || !noKeys) return null;

  return (
    <Alert
      severity="info"
      variant="outlined"
      sx={{ width: '100%', maxWidth: 640, mx: 'auto', mb: 3 }}
      // `action` replaces Alert's built-in close button, so dismiss lives next to the link.
      action={(
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Button component={RouterLink} to="/settings/apikeys" color="inherit" size="small" sx={{ whiteSpace: 'nowrap' }}>
            {t('startScreen.onboarding.action')}
          </Button>
          <IconButton size="small" color="inherit" aria-label={t('startScreen.onboarding.dismiss')} onClick={() => setDismissed(true)}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Box>
      )}
    >
      <AlertTitle>{t('startScreen.onboarding.title')}</AlertTitle>
      {t('startScreen.onboarding.body')}
    </Alert>
  );
}
