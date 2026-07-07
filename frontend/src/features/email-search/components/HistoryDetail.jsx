import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import IconButton from '@mui/material/IconButton';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

import FoundProvidersList from './FoundProvidersList';
import { emailSearchApi } from '../services/api/emailSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('EmailSearchHistoryDetail');
const STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };

export default function HistoryDetail() {
  const { t } = useTranslation('emailSearch');
  const { id } = useParams();
  const navigate = useNavigate();
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadRun = useCallback(async () => {
    try {
      setLoading(true);
      const data = await emailSearchApi.getRun(id);
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
        <IconButton onClick={() => navigate('/email-search/history')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5">{run.username}</Typography>
        <Chip size="small" label={t(`history.status.${run.status}`)} color={STATUS_COLORS[run.status] || 'default'} />
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t('history.summary', { checked: run.total_providers_checked, found: run.found_count })}
      </Typography>

      {run.status === 'failed' && run.error_message && (
        <Typography variant="body2" color="error" sx={{ mb: 2 }}>
          {run.error_message}
        </Typography>
      )}

      <FoundProvidersList providers={run.provider_results} />
    </Box>
  );
}
