import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router';
import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';
import { apiKeySettingsPath } from '../../utils/apiKeyLinks';


/**
 * "This needs an API key" notice whose action jumps straight to that service's key card,
 * instead of the full API Keys list. `actionLabel` overrides the default "Add API key".
 */
export default function ApiKeyRequiredAlert({ serviceKey, message, actionLabel, severity = 'info', sx }) {
  const { t } = useTranslation();
  return (
    <Alert
      severity={severity}
      variant="outlined"
      sx={{ borderRadius: 1, mb: 2, ...sx }}
      action={
        <Link
          component={RouterLink}
          to={apiKeySettingsPath(serviceKey)}
          underline="hover"
          sx={{ whiteSpace: 'nowrap', alignSelf: 'center' }}
        >
          {actionLabel ?? t('apiKeyAlert.addKey')}
        </Link>
      }
    >
      {message}
    </Alert>
  );
}
