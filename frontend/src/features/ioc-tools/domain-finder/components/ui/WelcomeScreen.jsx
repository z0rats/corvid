import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

export default function WelcomeScreen() {
  const { t } = useTranslation('iocTools');
  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" component="h1" gutterBottom>
          {t('domainFinder.welcomeScreen.title')}
        </Typography>
        <Typography sx={{ mb: 2 }}>
          {t('domainFinder.welcomeScreen.intro')}
        </Typography>
        <Typography sx={{ mb: 2 }}>
          {t('domainFinder.welcomeScreen.description')}
        </Typography>
        <Typography variant="body2" sx={{
          p: 2,
          borderRadius: 1,
          fontFamily: 'monospace'
        }}>
          {t('domainFinder.welcomeScreen.example')}
        </Typography>
      </Box>

      <Typography variant="h6" sx={{ mb: 2 }}>
        {t('domainFinder.welcomeScreen.featuresTitle')}
      </Typography>

      <Grid container spacing={1}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">{t('domainFinder.welcomeScreen.features.patternMatching.title')}</Typography>
            <Typography variant="body2" color="text.secondary">
              {t('domainFinder.welcomeScreen.features.patternMatching.description')}
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">{t('domainFinder.welcomeScreen.features.safePreview.title')}</Typography>
            <Typography variant="body2" color="text.secondary">
              {t('domainFinder.welcomeScreen.features.safePreview.description')}
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">{t('domainFinder.welcomeScreen.features.threatIntelligence.title')}</Typography>
            <Typography variant="body2" color="text.secondary">
              {t('domainFinder.welcomeScreen.features.threatIntelligence.description')}
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">{t('domainFinder.welcomeScreen.features.proactiveDefense.title')}</Typography>
            <Typography variant="body2" color="text.secondary">
              {t('domainFinder.welcomeScreen.features.proactiveDefense.description')}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
}
