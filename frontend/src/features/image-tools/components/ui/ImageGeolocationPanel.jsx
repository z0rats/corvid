import React from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Grow from '@mui/material/Grow';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import PublicIcon from '@mui/icons-material/Public';
import { useImageGeolocation } from '../../hooks/api/useImageGeolocation';

function confidenceColor(confidence) {
  if (confidence >= 0.6) return 'success';
  if (confidence >= 0.3) return 'warning';
  return 'default';
}

export default function ImageGeolocationPanel({ file }) {
  const { t } = useTranslation('imageTools');
  const { result, loading, error, hasLlmKey, geolocateImage } = useImageGeolocation();

  if (!hasLlmKey || !file) {
    return null;
  }

  return (
    <Card variant="outlined" sx={{ mt: 2, p: 2 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={1}>
        <Box display="flex" alignItems="center">
          <PublicIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="subtitle1" fontWeight="medium">{t('geolocation.title')}</Typography>
        </Box>
        <Button
          variant="contained"
          disableElevation
          size="small"
          disabled={loading}
          onClick={() => geolocateImage(file)}
        >
          {t('geolocation.analyzeButton')}
        </Button>
      </Box>

      {loading && <LinearProgress sx={{ mt: 1.5 }} />}
      {error && <Alert severity="error" sx={{ mt: 1.5 }}>{error}</Alert>}

      {result && (
        <Grow in>
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              {t('geolocation.modelUsed', { model: result.model_used })}
            </Typography>

            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
              {t('geolocation.candidates')}
            </Typography>
            {result.candidates.map((candidate) => (
              <Box
                key={candidate.location}
                sx={{ mb: 1.5, p: 1.5, borderRadius: 1, border: '1px solid', borderColor: 'divider' }}
              >
                <Box display="flex" alignItems="center" justifyContent="space-between" gap={1}>
                  <Typography variant="body1" fontWeight="medium">{candidate.location}</Typography>
                  <Chip
                    size="small"
                    label={`${Math.round(candidate.confidence * 100)}%`}
                    color={confidenceColor(candidate.confidence)}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {candidate.reasoning}
                </Typography>
              </Box>
            ))}

            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
              {t('geolocation.clues')}
            </Typography>
            {result.clues.map((clue) => (
              <Box key={`${clue.category}-${clue.observation}`} sx={{ mb: 1 }}>
                <Chip size="small" variant="outlined" label={clue.category} sx={{ mr: 1, mb: 0.5 }} />
                <Typography variant="body2" component="span" color="text.secondary">
                  {clue.observation} — {clue.supports}
                </Typography>
              </Box>
            ))}

            {result.caveats && (
              <Alert severity="info" sx={{ mt: 2 }}>{result.caveats}</Alert>
            )}
          </Box>
        </Grow>
      )}
    </Card>
  );
}
