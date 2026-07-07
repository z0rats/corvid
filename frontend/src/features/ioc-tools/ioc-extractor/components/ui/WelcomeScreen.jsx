import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

export default function ExtractorWelcomeScreen() {
  const { t } = useTranslation('iocTools');

  const features = [
    {
      title: t('iocExtractor.welcomeScreen.features.automatedExtraction.title'),
      description: t('iocExtractor.welcomeScreen.features.automatedExtraction.description')
    },
    {
      title: t('iocExtractor.welcomeScreen.features.duplicateRemoval.title'),
      description: t('iocExtractor.welcomeScreen.features.duplicateRemoval.description')
    },
    {
      title: t('iocExtractor.welcomeScreen.features.simpleInterface.title'),
      description: t('iocExtractor.welcomeScreen.features.simpleInterface.description')
    },
    {
      title: t('iocExtractor.welcomeScreen.features.oneClickAnalysis.title'),
      description: t('iocExtractor.welcomeScreen.features.oneClickAnalysis.description')
    }
  ];

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        {t('iocExtractor.welcomeScreen.title')}
      </Typography>

      <Box sx={{ mb: 4 }}>
        <Typography sx={{ mb: 2 }}>
          {t('iocExtractor.welcomeScreen.intro')}
        </Typography>
        <Typography>
          {t('iocExtractor.welcomeScreen.usage')}
        </Typography>
      </Box>

      <Typography variant="h6" sx={{ mb: 2 }}>
        {t('iocExtractor.welcomeScreen.keyFeatures')}
      </Typography>

      <Grid container spacing={1}>
        {features.map((feature, index) => (
          <Grid size={{ xs: 12, sm: 6 }} key={index}>
            <Paper elevation={0} sx={{ p: 1 }}>
              <Typography color="primary" fontWeight="medium">
                {feature.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {feature.description}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
}
