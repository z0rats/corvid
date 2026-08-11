import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';

import HistoryDetailHeader from '../../../core/components/HistoryDetailHeader';
import { useHistoryDetail } from '../../../core/hooks/useHistoryDetail';
import ResultsView from './ResultsView';
import { gitReconApi } from '../services/api/gitReconApi';

const STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };

export default function HistoryDetail() {
  const { t } = useTranslation('gitRecon');
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: search, loading } = useHistoryDetail(gitReconApi.getHistory, id);

  if (loading) return <LinearProgress />;
  if (!search) return <Typography color="text.secondary">{t('history.notFound')}</Typography>;

  return (
    <Box>
      <HistoryDetailHeader
        onBack={() => navigate('/git-recon/history')}
        title={search.target}
        chips={<Chip size="small" label={t(`history.status.${search.status}`)} color={STATUS_COLORS[search.status] || 'default'} />}
        summary={t('history.summary', { mode: t(`form.modes.${search.mode}`), date: new Date(search.searched_at).toLocaleString() })}
        error={search.status === 'failed' ? search.error : null}
      />

      <ResultsView result={search.result} />
    </Box>
  );
}
