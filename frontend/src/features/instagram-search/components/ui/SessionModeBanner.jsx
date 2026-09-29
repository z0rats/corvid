import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router';
import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';

export default function SessionModeBanner({ mode }) {
  const { t } = useTranslation('instagramSearch');
  const isSession = mode === 'session';

  return (
    <Alert
      severity={isSession ? 'warning' : 'info'}
      variant="outlined"
      sx={{ borderRadius: 1, mb: 2 }}
      action={
        !isSession && (
          <Link component={RouterLink} to="/settings/apikeys" underline="hover" sx={{ whiteSpace: 'nowrap', alignSelf: 'center' }}>
            {t('mode.configureSessionAction')}
          </Link>
        )
      }
    >
      {isSession ? t('mode.sessionWarning') : t('mode.anonymousInfo')}
    </Alert>
  );
}
