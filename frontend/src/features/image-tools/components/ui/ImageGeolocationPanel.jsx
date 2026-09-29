import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Grow from '@mui/material/Grow';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import DownloadIcon from '@mui/icons-material/Download';
import HistoryIcon from '@mui/icons-material/History';
import PublicIcon from '@mui/icons-material/Public';
import GeolocationHistoryList from './GeolocationHistoryList';
import { useImageGeolocation } from '../../hooks/api/useImageGeolocation';
import { geolocationHistoryApi } from '../../services/api/geolocationHistoryApi';

const REPORT_FORMATS = ['html', 'pdf'];

function confidenceColor(confidence) {
  if (confidence >= 0.6) return 'success';
  if (confidence >= 0.3) return 'warning';
  return 'default';
}

export default function ImageGeolocationPanel({ file }) {
  const { t } = useTranslation('imageTools');
  const { result, loading, error, hasLlmKey, geolocateImage } = useImageGeolocation();
  const [viewedResult, setViewedResult] = useState(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  useEffect(() => {
    if (result) {
      setViewedResult(result);
      setHistoryOpen(false);
    }
  }, [result]);

  const handleSelectHistoryRow = async (row) => {
    const detail = await geolocationHistoryApi.getSearch(row.id);
    setViewedResult({ ...detail.result, model_used: detail.model_used, history_id: detail.id });
    setHistoryOpen(false);
  };

  if (!hasLlmKey || !file) {
    return null;
  }

  return (
    <Card variant="outlined" sx={{ mt: 2, p: 2 }}>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 1
        }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center"
          }}>
          <PublicIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="subtitle1" fontWeight="medium">{t('geolocation.title')}</Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            size="small"
            startIcon={<HistoryIcon />}
            onClick={() => setHistoryOpen((open) => !open)}
          >
            {historyOpen ? t('geolocation.hideHistoryButton') : t('geolocation.historyButton')}
          </Button>
          <Button
            variant="contained"
            disableElevation
            size="small"
            disabled={loading}
            onClick={() => geolocateImage(file)}
          >
            {t('geolocation.analyzeButton')}
          </Button>
        </Stack>
      </Box>

      {historyOpen && (
        <Box sx={{ mt: 2 }}>
          <GeolocationHistoryList onSelect={handleSelectHistoryRow} />
        </Box>
      )}

      {loading && <LinearProgress sx={{ mt: 1.5 }} />}
      {error && <Alert severity="error" sx={{ mt: 1.5 }}>{error}</Alert>}

      {viewedResult && (
        <Grow in>
          <Box sx={{ mt: 2 }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: 1
              }}>
              <Typography variant="caption" color="text.secondary">
                {t('geolocation.modelUsed', { model: viewedResult.model_used })}
              </Typography>
              {viewedResult.history_id != null && (
                <Stack direction="row" spacing={1}>
                  {REPORT_FORMATS.map((fmt) => (
                    <Button
                      key={fmt}
                      size="small"
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      component="a"
                      href={geolocationHistoryApi.reportUrl(viewedResult.history_id, fmt)}
                      download
                    >
                      {fmt.toUpperCase()}
                    </Button>
                  ))}
                </Stack>
              )}
            </Box>

            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
              {t('geolocation.candidates')}
            </Typography>
            {viewedResult.candidates.map((candidate) => (
              <Box
                key={candidate.location}
                sx={{ mb: 1.5, p: 1.5, borderRadius: 1, border: '1px solid', borderColor: 'divider' }}
              >
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 1
                  }}>
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
            {viewedResult.clues.map((clue) => (
              <Box key={`${clue.category}-${clue.observation}`} sx={{ mb: 1 }}>
                <Chip size="small" variant="outlined" label={clue.category} sx={{ mr: 1, mb: 0.5 }} />
                <Typography variant="body2" component="span" color="text.secondary">
                  {clue.observation} — {clue.supports}
                </Typography>
              </Box>
            ))}

            {viewedResult.caveats && (
              <Alert severity="info" sx={{ mt: 2 }}>{viewedResult.caveats}</Alert>
            )}
          </Box>
        </Grow>
      )}
    </Card>
  );
}
