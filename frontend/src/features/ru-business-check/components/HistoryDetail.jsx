import { useParams, useNavigate } from 'react-router';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';

import HistoryDetailHeader from '../../../core/components/HistoryDetailHeader';
import { useHistoryDetail } from '../../../core/hooks/useHistoryDetail';
import ResultsView from './ResultsView';
import ReportExportButtons from './ReportExportButtons';
import { ruBusinessCheckApi } from '../services/api/ruBusinessCheckApi';

const STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };
const STATUS_LABELS = { running: 'Выполняется', completed: 'Завершено', cancelled: 'Отменено', failed: 'Ошибка' };

export default function HistoryDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: search, loading } = useHistoryDetail(ruBusinessCheckApi.getHistory, id);

  if (loading) return <LinearProgress />;
  if (!search) return <Typography color="text.secondary">Проверка не найдена</Typography>;

  return (
    <>
      <HistoryDetailHeader
        onBack={() => navigate('/ru-business-check/history')}
        title={search.query}
        chips={<Chip size="small" label={STATUS_LABELS[search.status] || search.status} color={STATUS_COLORS[search.status] || 'default'} />}
        summary={`Проверено ${new Date(search.searched_at).toLocaleString()}`}
        error={search.status === 'failed' ? search.error : null}
      />

      {search.status === 'completed' && <ReportExportButtons searchId={search.id} />}

      <ResultsView result={search} />
    </>
  );
}
