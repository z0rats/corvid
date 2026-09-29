import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';

import HistoryDetailHeader from '../../../core/components/HistoryDetailHeader';
import { useHistoryDetail } from '../../../core/hooks/useHistoryDetail';
import ResultsView from './ResultsView';
import { amassApi } from '../services/api/amassApi';
import ScanStatusChip from '../../../core/components/ScanStatusChip';


export default function HistoryDetail() {
  const { t } = useTranslation('amass');
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: search, loading } = useHistoryDetail(amassApi.getHistory, id);

  if (loading) return <LinearProgress />;
  if (!search) return <Typography color="text.secondary">{t('history.notFound')}</Typography>;

  return (
    <Box>
      <HistoryDetailHeader
        onBack={() => navigate('/amass/history')}
        title={search.domain}
        chips={<ScanStatusChip status={search.status} label={t(`history.status.${search.status}`)} />}
        summary={t('history.summary', { date: new Date(search.searched_at).toLocaleString() })}
        error={search.status === 'failed' ? search.error : null}
      />

      <ResultsView result={search.result} />
    </Box>
  );
}
