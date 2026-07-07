import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

export default function WelcomeScreen() {
  const { t } = useTranslation('emailAnalyzer');

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        {t('welcomeScreen.title')}
      </Typography>
      <Box sx={{ mb: 4 }}>
        <Typography sx={{ mb: 2 }}>
          {t('welcomeScreen.description1')}
        </Typography>
        <Typography>
          {t('welcomeScreen.description2')}
        </Typography>
      </Box>

      <Typography variant="h6" sx={{ mb: 2 }}>
        {t('welcomeScreen.keyFeaturesTitle')}
      </Typography>

      <Grid container spacing={1}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              {t('welcomeScreen.features.securityAnalysis.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('welcomeScreen.features.securityAnalysis.description')}
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              {t('welcomeScreen.features.iocExtraction.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('welcomeScreen.features.iocExtraction.description')}
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              {t('welcomeScreen.features.attachmentAnalysis.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('welcomeScreen.features.attachmentAnalysis.description')}
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              {t('welcomeScreen.features.privacyFriendly.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('welcomeScreen.features.privacyFriendly.description')}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
}
