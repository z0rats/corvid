import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Chip from '@mui/material/Chip';

import HistoryTable from '../../../core/components/HistoryTable';
import { instagramSearchApi } from '../services/api/instagramSearchApi';
import ScanStatusChip from '../../../core/components/ScanStatusChip';


export default function HistoryList() {
  const { t } = useTranslation('instagramSearch');
  const navigate = useNavigate();

  const columns = [
    {
      key: 'scan_type',
      header: t('history.headers.scanType'),
      render: (search) => <Chip size="small" label={t(`scanForm.types.${search.scan_type}`)} />,
    },
    { key: 'username', header: t('history.headers.username') },
    {
      key: 'status',
      header: t('history.headers.status'),
      render: (search) => (
        <ScanStatusChip status={search.status} label={t(`history.status.${search.status}`)} />
      ),
    },
    {
      key: 'item_count',
      header: t('history.headers.items'),
      render: (search) => (
        search.total_count != null ? `${search.item_count}/${search.total_count}` : search.item_count
      ),
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
      fetchRows={instagramSearchApi.listHistory}
      onDelete={instagramSearchApi.deleteHistory}
      onRowClick={(search) => navigate(`/instagram-search/history/${search.id}`)}
      emptyText={t('history.empty')}
      actionsLabel={t('history.headers.actions')}
    />
  );
}
