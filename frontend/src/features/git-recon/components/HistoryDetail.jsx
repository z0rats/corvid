import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import IconButton from '@mui/material/IconButton';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

import ResultsView from './ResultsView';
import { gitReconApi } from '../services/api/gitReconApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('GitReconHistoryDetail');

export default function HistoryDetail() {
  const { t } = useTranslation('gitRecon');
  const { id } = useParams();
  const navigate = useNavigate();
  const [search, setSearch] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadSearch = useCallback(async () => {
    try {
      setLoading(true);
      const data = await gitReconApi.getHistory(id);
      setSearch(data);
    } catch (err) {
      logger.error('Failed to load search:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { loadSearch(); }, [loadSearch]);

  if (loading) return <LinearProgress />;
  if (!search) return <Typography color="text.secondary">{t('history.notFound')}</Typography>;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <IconButton onClick={() => navigate('/git-recon/history')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5">{search.target}</Typography>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('history.summary', { mode: t(`form.modes.${search.mode}`), date: new Date(search.searched_at).toLocaleString() })}
      </Typography>

      <ResultsView result={search.result} />
    </Box>
  );
}
