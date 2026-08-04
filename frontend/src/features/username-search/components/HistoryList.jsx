import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Chip from '@mui/material/Chip';

import HistoryTable from '../../../core/components/HistoryTable';
import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { sourceLabelKey } from '../utils/sourceLabels';

const STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };

export default function HistoryList() {
  const { t } = useTranslation('usernameSearch');
  const navigate = useNavigate();

  const columns = [
    { key: 'username', header: t('history.headers.username') },
    {
      key: 'source',
      header: t('history.headers.source'),
      render: (run) => (
        <Chip
          size="small"
          variant="outlined"
          label={t(sourceLabelKey(run.source))}
        />
      ),
    },
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
      fetchRows={usernameSearchApi.listRuns}
      onDelete={usernameSearchApi.deleteRun}
      onRowClick={(run) => navigate(`/username-search/history/${run.id}`)}
      emptyText={t('history.empty')}
      actionsLabel={t('history.headers.actions')}
    />
  );
}
