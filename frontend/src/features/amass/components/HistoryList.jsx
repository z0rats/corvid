import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';

import HistoryTable from '../../../core/components/HistoryTable';
import { amassApi } from '../services/api/amassApi';
import ScanStatusChip from '../../../core/components/ScanStatusChip';


export default function HistoryList() {
  const { t } = useTranslation('amass');
  const navigate = useNavigate();

  const columns = [
    { key: 'domain', header: t('history.headers.domain') },
    {
      key: 'status',
      header: t('history.headers.status'),
      render: (search) => (
        <ScanStatusChip status={search.status} label={t(`history.status.${search.status}`)} />
      ),
    },
    { key: 'hosts_found', header: t('history.headers.hosts') },
    {
      key: 'brute_force',
      header: t('history.headers.bruteForce'),
      render: (search) => (search.brute_force ? t('form.bruteForceLabel') : '-'),
    },
    {
      key: 'searched_at',
      header: t('history.headers.searched'),
      render: (search) => new Date(search.searched_at).toLocaleString(),
    },
  ];

  return (
    <HistoryTable
      columns={columns}
      fetchRows={amassApi.listHistory}
      onDelete={amassApi.deleteHistory}
      onRowClick={(search) => navigate(`/amass/history/${search.id}`)}
      emptyText={t('history.empty')}
      actionsLabel={t('history.headers.actions')}
    />
  );
}
