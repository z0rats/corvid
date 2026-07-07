import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

const SUPPORTED_IOC_TYPE_KEYS = [
  'ipAddresses',
  'domains',
  'urls',
  'emailAddresses',
  'hashes',
  'cves',
];

const FeatureCard = ({ title, description }) => (
  <Grid size={{ xs: 12, sm: 6 }} key={title}>
    <Paper elevation={0} sx={{ p: 1.5 }}>
      <Typography color="primary" fontWeight="medium" sx={{ fontSize: '0.9rem' }}>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
        {description}
      </Typography>
    </Paper>
  </Grid>
);

export default function WelcomeScreen() {
  const { t } = useTranslation('iocTools');

  return (
    <Paper sx={{ p: { xs: 2, sm: 3 }, mt: 2 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" component="h1" gutterBottom>
          {t('bulkLookup.welcomeScreen.title')}
        </Typography>
        <Typography sx={{ mb: 2 }}>
          {t('bulkLookup.welcomeScreen.intro')}
        </Typography>
        <Typography>
          {t('bulkLookup.welcomeScreen.instructions')}
        </Typography>
      </Box>

      <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
        {t('bulkLookup.welcomeScreen.supportedTypesHeading')}
      </Typography>
      <Grid container spacing={1}>
        {SUPPORTED_IOC_TYPE_KEYS.map(key => (
          <FeatureCard
            key={key}
            title={t(`bulkLookup.welcomeScreen.supportedTypes.${key}.title`)}
            description={t(`bulkLookup.welcomeScreen.supportedTypes.${key}.description`)}
          />
        ))}
      </Grid>
    </Paper>
  );
}
