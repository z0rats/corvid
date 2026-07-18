import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';

export default function EngineWarningBanner() {
  const { t } = useTranslation('dorkRunner');
  return (
    <Alert severity="warning" sx={{ mb: 2 }}>
      <AlertTitle>{t('engineWarning.title')}</AlertTitle>
      {t('engineWarning.message')}
    </Alert>
  );
}
