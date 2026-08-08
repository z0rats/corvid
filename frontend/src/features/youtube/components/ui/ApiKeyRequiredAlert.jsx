import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router';
import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';

export default function ApiKeyRequiredAlert({ message }) {
  const { t } = useTranslation('youtube');
  return (
    <Alert
      severity="info"
      variant="outlined"
      sx={{ borderRadius: 1, mb: 2 }}
      action={
        <Link component={RouterLink} to="/settings/apikeys" underline="hover" sx={{ whiteSpace: 'nowrap', alignSelf: 'center' }}>
          {t('apiKey.addKeyAction')}
        </Link>
      }
    >
      {message}
    </Alert>
  );
}
