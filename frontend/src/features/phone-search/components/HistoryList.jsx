import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Chip from '@mui/material/Chip';

import HistoryTable from '../../../core/components/HistoryTable';
import { phoneSearchApi } from '../services/api/phoneSearchApi';

const STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };

export default function HistoryList() {
  const { t } = useTranslation('phoneSearch');
  const navigate = useNavigate();

  const columns = [
    { key: 'phone_number', header: t('history.headers.phoneNumber') },
    {
      key: 'status',
      header: t('history.headers.status'),
      render: (run) => (
        <Chip size="small" label={t(`history.status.${run.status}`)} color={STATUS_COLORS[run.status] || 'default'} />
      ),
    },
    { key: 'found_count', header: t('history.headers.found') },
    {
      key: 'started_at',
      header: t('history.headers.started'),
      render: (run) => new Date(run.started_at).toLocaleString(),
    },
  ];

  return (
    <HistoryTable
      columns={columns}
      fetchRows={phoneSearchApi.listRuns}
      onDelete={phoneSearchApi.deleteRun}
      onRowClick={(run) => navigate(`/phone-search/history/${run.id}`)}
      emptyText={t('history.empty')}
      actionsLabel={t('history.headers.actions')}
    />
  );
}
