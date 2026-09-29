import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';

import HistoryDetailHeader from '../../../core/components/HistoryDetailHeader';
import { useHistoryDetail } from '../../../core/hooks/useHistoryDetail';
import ResultsView from './ResultsView';
import { instagramSearchApi } from '../services/api/instagramSearchApi';

const STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };

export default function HistoryDetail() {
  const { t } = useTranslation('instagramSearch');
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: search, loading } = useHistoryDetail(instagramSearchApi.getHistory, id);

  if (loading) return <LinearProgress />;
  if (!search) return <Typography color="text.secondary">{t('history.notFound')}</Typography>;

  return (
    <>
      <HistoryDetailHeader
        onBack={() => navigate('/instagram-search/history')}
        title={`@${search.username}`}
        chips={<Chip size="small" label={t(`history.status.${search.status}`)} color={STATUS_COLORS[search.status] || 'default'} />}
        summary={t('history.summary', { scanType: t(`scanForm.types.${search.scan_type}`), date: new Date(search.searched_at).toLocaleString() })}
        error={search.status === 'failed' ? search.error : null}
      />

      <ResultsView result={search} />
    </>
  );
}
