import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';

import HistoryTable from '../../../core/components/HistoryTable';
import { emailSearchApi } from '../services/api/emailSearchApi';
import ScanStatusChip from '../../../core/components/ScanStatusChip';


export default function HistoryList() {
  const { t } = useTranslation('emailSearch');
  const navigate = useNavigate();

  const columns = [
    { key: 'username', header: t('history.headers.username') },
    {
      key: 'status',
      header: t('history.headers.status'),
      render: (run) => (
        <ScanStatusChip status={run.status} label={t(`history.status.${run.status}`)} />
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
      fetchRows={emailSearchApi.listRuns}
      onDelete={emailSearchApi.deleteRun}
      onRowClick={(run) => navigate(`/email-search/history/${run.id}`)}
      emptyText={t('history.empty')}
      actionsLabel={t('history.headers.actions')}
    />
  );
}
