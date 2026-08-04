import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import PhotoCameraIcon from '@mui/icons-material/PhotoCamera';

const SAMPLE_PHOTO_URL = '/sample/corvid-sample.jpg';
const SAMPLE_PHOTO_FILENAME = 'corvid-sample.jpg';

export default function WelcomeScreen({ onTrySample }) {
  const { t } = useTranslation('imageTools');
  const [loadingSample, setLoadingSample] = useState(false);

  const handleTrySample = async () => {
    setLoadingSample(true);
    try {
      const response = await fetch(SAMPLE_PHOTO_URL);
      const blob = await response.blob();
      const file = new File([blob], SAMPLE_PHOTO_FILENAME, { type: 'image/jpeg' });
      await onTrySample(file);
    } finally {
      setLoadingSample(false);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        {t('welcome.title')}
      </Typography>
      <Box sx={{ mb: 3 }}>
        <Typography sx={{ mb: 2 }}>
          {t('welcome.intro1')}
        </Typography>
        <Typography>
          {t('welcome.intro2')}
        </Typography>
      </Box>

      <Box sx={{ mb: 4, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 0.75 }}>
        <Button
          variant="outlined"
          startIcon={loadingSample ? <CircularProgress size={16} /> : <PhotoCameraIcon />}
          disabled={loadingSample}
          onClick={handleTrySample}
        >
          {loadingSample ? t('welcome.sampleLoading') : t('welcome.sampleButton')}
        </Button>
        <Typography variant="caption" color="text.secondary">
          {t('welcome.sampleCaption')}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {t('welcome.sampleHint')}
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
