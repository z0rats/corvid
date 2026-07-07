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
  'cryptoAddresses',
];

const ADDRESS_REPUTATION_CHECK_KEYS = [
  'ofacSdn',
  'scamSniffer',
];

const FeatureCard = ({ title, description }) => (
  <Grid size={{ xs: 12, sm: 6 }} key={title}>
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
    <Paper sx={{ p: { xs: 2, sm: 3 } }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" component="h1" gutterBottom>
          {t('singleLookup.welcomeScreen.title')}
        </Typography>
        <Typography sx={{ mb: 2 }}>
          {t('singleLookup.welcomeScreen.intro')}
        </Typography>
        <Typography>
          {t('singleLookup.welcomeScreen.description')}
        </Typography>
      </Box>

      <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
        {t('singleLookup.welcomeScreen.supportedIocTypesTitle')}
      </Typography>
      <Grid container spacing={1}>
        {SUPPORTED_IOC_TYPE_KEYS.map(key => (
          <FeatureCard
            key={key}
            title={t(`singleLookup.welcomeScreen.iocTypes.${key}.title`)}
            description={t(`singleLookup.welcomeScreen.iocTypes.${key}.description`)}
          />
        ))}
      </Grid>

      <Typography variant="h6" component="h2" sx={{ mt: 4, mb: 2 }}>
        {t('singleLookup.welcomeScreen.addressReputationChecksTitle')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('singleLookup.welcomeScreen.addressReputationChecksIntro')}
      </Typography>
      <Grid container spacing={1}>
        {ADDRESS_REPUTATION_CHECK_KEYS.map(key => (
          <FeatureCard
            key={key}
            title={t(`singleLookup.welcomeScreen.addressReputationChecks.${key}.title`)}
            description={t(`singleLookup.welcomeScreen.addressReputationChecks.${key}.description`)}
          />
        ))}
      </Grid>
    </Paper>
  );
}