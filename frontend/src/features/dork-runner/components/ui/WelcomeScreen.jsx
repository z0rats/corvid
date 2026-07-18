import { useTranslation } from 'react-i18next';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

export default function WelcomeScreen() {
  const { t } = useTranslation('dorkRunner');
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" component="h1" gutterBottom>
        {t('welcomeScreen.title')}
      </Typography>
      <Typography sx={{ mb: 1 }}>
        {t('welcomeScreen.intro')}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {t('welcomeScreen.description')}
      </Typography>
    </Paper>
  );
}
