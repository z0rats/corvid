import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Grow from '@mui/material/Grow';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';

import ApiKeyRequiredAlert from './components/ui/ApiKeyRequiredAlert';
import CommentsPanel from './components/ui/CommentsPanel';
import ThumbnailGrid from './components/ui/ThumbnailGrid';
import VideoOverviewCard from './components/ui/VideoOverviewCard';
import VideoStatsCard from './components/ui/VideoStatsCard';
import WelcomeScreen from './components/ui/WelcomeScreen';
import { useYoutubeLookup } from './hooks/ui/useYoutubeLookup';

export default function YoutubeLookup() {
  const { t } = useTranslation('youtube');
  const { url, setUrl, result, loading, error, lookupVideo } = useYoutubeLookup();

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      lookupVideo();
    }
  };

  return (
    <>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField
            fullWidth
            size="small"
            label={t('form.urlLabel')}
            placeholder={t('form.urlPlaceholder')}
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <Box>
            <Button
              variant="contained"
              onClick={() => lookupVideo()}
              disabled={loading || !url.trim()}
              sx={{ whiteSpace: 'nowrap' }}
            >
              {loading ? <CircularProgress size={20} /> : t('form.lookupButton')}
            </Button>
          </Box>
        </Stack>
      </Paper>

      {error && (
        <Grow in={true}>
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        </Grow>
      )}

      {result ? (
        <>
          <VideoOverviewCard result={result} />
          {!result.api_configured && <ApiKeyRequiredAlert message={t('apiKey.notConfigured')} />}
          <VideoStatsCard result={result} />
          <CommentsPanel result={result} />
          <ThumbnailGrid thumbnails={result.thumbnails} />
        </>
      ) : (
        !loading && <WelcomeScreen />
      )}
    </>
  );
}
