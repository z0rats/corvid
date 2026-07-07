import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import { useTranslation } from 'react-i18next';
import { SUPPORTED_DEFANGING_TECHNIQUES } from '../../constants/defangerConstants';

const FeatureCard = ({ title, description }) => (
  <Grid size={{ xs: 12, sm: 6 }}>
    <Paper elevation={0} sx={{ p: 1 }}>
      <Typography color="primary" fontWeight="medium">
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {description}
      </Typography>
    </Paper>
  </Grid>
);

export default function WelcomeScreen() {
  const { t } = useTranslation('iocTools');

  return (
    <Paper>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" component="h1" gutterBottom mb={2}>
          {t('iocDefanger.welcomeScreen.title')}
        </Typography>
        <Typography variant="h6" component="h1" gutterBottom>
          {t('iocDefanger.welcomeScreen.subtitle')}
        </Typography>
        <Typography sx={{ mb: 2 }}>
          {t('iocDefanger.welcomeScreen.description')}
        </Typography>
      </Box>
      <Grid container spacing={1}>
        {SUPPORTED_DEFANGING_TECHNIQUES.map((item) => (
          <FeatureCard key={item.title} title={item.title} description={item.description} />
        ))}
      </Grid>
    </Paper>
  );
}
