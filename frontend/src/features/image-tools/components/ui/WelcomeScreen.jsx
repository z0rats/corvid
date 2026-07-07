import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

export default function WelcomeScreen() {
  const { t } = useTranslation('imageTools');

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        {t('welcome.title')}
      </Typography>
      <Box sx={{ mb: 4 }}>
        <Typography sx={{ mb: 2 }}>
          {t('welcome.intro1')}
        </Typography>
        <Typography>
          {t('welcome.intro2')}
        </Typography>
      </Box>

      <Typography variant="h6" sx={{ mb: 2 }}>
        {t('welcome.keyFeatures')}
      </Typography>

      <Grid container spacing={1}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              {t('welcome.exifGps.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('welcome.exifGps.description')}
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              {t('welcome.fileProps.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('welcome.fileProps.description')}
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              {t('welcome.reverseSearch.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('welcome.reverseSearch.description')}
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              {t('welcome.privacy.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('welcome.privacy.description')}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
}
