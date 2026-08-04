import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Chip from '@mui/material/Chip';

import HistoryTable from '../../../core/components/HistoryTable';
import { gitReconApi } from '../services/api/gitReconApi';

const STATUS_COLORS = { running: 'info', completed: 'success', failed: 'error' };

export default function HistoryList() {
  const { t } = useTranslation('gitRecon');
  const navigate = useNavigate();

  const columns = [
    {
      key: 'mode',
      header: t('history.headers.mode'),
      render: (search) => <Chip size="small" label={t(`form.modes.${search.mode}`)} />,
    },
    { key: 'target', header: t('history.headers.target') },
    {
      key: 'status',
      header: t('history.headers.status'),
      render: (search) => (
        <Chip size="small" label={t(`history.status.${search.status}`)} color={STATUS_COLORS[search.status] || 'default'} />
      ),
    },
    { key: 'persons_found', header: t('history.headers.persons') },
    {
      key: 'repos',
      header: t('history.headers.repos'),
      render: (search) => (search.mode === 'search' ? '-' : `${search.repos_scanned}/${search.repos_scanned + search.repos_failed}`),
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
      fetchRows={gitReconApi.listHistory}
      onDelete={gitReconApi.deleteHistory}
      onRowClick={(search) => navigate(`/git-recon/history/${search.id}`)}
      emptyText={t('history.empty')}
      actionsLabel={t('history.headers.actions')}
    />
  );
}
