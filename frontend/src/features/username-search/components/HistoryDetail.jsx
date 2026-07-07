import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import LinearProgress from '@mui/material/LinearProgress';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DownloadIcon from '@mui/icons-material/Download';

import FoundSitesList from './FoundSitesList';
import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('UsernameSearchHistoryDetail');
const STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };
const EXPORT_FORMATS = ['csv', 'txt', 'json', 'html', 'pdf', 'xmind'];

export default function HistoryDetail() {
  const { t } = useTranslation('usernameSearch');
  const { id } = useParams();
  const navigate = useNavigate();
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadRun = useCallback(async () => {
    try {
      setLoading(true);
      const data = await usernameSearchApi.getRun(id);
      setRun(data);
    } catch (err) {
      logger.error('Failed to load search run:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { loadRun(); }, [loadRun]);

  if (loading) return <LinearProgress />;
  if (!run) return <Typography color="text.secondary">{t('history.notFound')}</Typography>;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <IconButton onClick={() => navigate('/username-search/history')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5">{run.username}</Typography>
        <Chip size="small" variant="outlined" label={t(`form.source${run.source === 'social_analyzer' ? 'SocialAnalyzer' : 'Maigret'}`)} />
        <Chip size="small" label={t(`history.status.${run.status}`)} color={STATUS_COLORS[run.status] || 'default'} />
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t('history.summary', { checked: run.total_sites_checked, found: run.found_count })}
      </Typography>

      {run.status === 'failed' && run.error_message && (
        <Typography variant="body2" color="error" sx={{ mb: 2 }}>
          {run.error_message}
        </Typography>
      )}

      {run.tags && run.tags.length > 0 && (
        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">{t('history.tagsUsed')}:</Typography>
          {run.tags.map((tag) => <Chip key={tag} size="small" label={tag} variant="outlined" />)}
        </Stack>
      )}

      {run.has_export && (
        <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap' }}>
          {EXPORT_FORMATS.map((fmt) => (
            <Button
              key={fmt}
              size="small"
              variant="outlined"
              startIcon={<DownloadIcon />}
              component="a"
              href={usernameSearchApi.exportUrl(run.id, fmt)}
              download
            >
              {fmt.toUpperCase()}
            </Button>
          ))}
        </Stack>
      )}

      <FoundSitesList sites={run.site_results} />
    </Box>
  );
}
