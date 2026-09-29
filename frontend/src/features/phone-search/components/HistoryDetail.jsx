import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';

import HistoryDetailHeader from '../../../core/components/HistoryDetailHeader';
import { useHistoryDetail } from '../../../core/hooks/useHistoryDetail';
import FoundProvidersList from './FoundProvidersList';
import { phoneSearchApi } from '../services/api/phoneSearchApi';

const STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };

export default function HistoryDetail() {
  const { t } = useTranslation('phoneSearch');
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: run, loading } = useHistoryDetail(phoneSearchApi.getRun, id);

  if (loading) return <LinearProgress />;
  if (!run) return <Typography color="text.secondary">{t('history.notFound')}</Typography>;

  return (
    <Box>
      <HistoryDetailHeader
        onBack={() => navigate('/phone-search/history')}
        title={run.phone_number}
        chips={<Chip size="small" label={t(`history.status.${run.status}`)} color={STATUS_COLORS[run.status] || 'default'} />}
        summary={t('history.summary', { checked: run.total_providers_checked, found: run.found_count })}
        error={run.status === 'failed' ? run.error_message : null}
      />

      <FoundProvidersList providers={run.provider_results} />
    </Box>
  );
}
