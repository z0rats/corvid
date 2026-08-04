import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Chip from '@mui/material/Chip';

import HistoryTable from '../../../../../../core/components/HistoryTable';
import { lookupHistoryApi } from '../../services/api/lookupHistoryApi';

export default function HistoryList() {
  const { t } = useTranslation('iocTools');
  const navigate = useNavigate();

  const columns = [
    { key: 'ioc', header: t('singleLookup.history.headers.ioc'), cellSx: { wordBreak: 'break-all' } },
    {
      key: 'ioc_type',
      header: t('singleLookup.history.headers.iocType'),
      render: (search) => <Chip size="small" label={search.ioc_type} variant="outlined" />,
    },
    {
      key: 'searched_at',
      header: t('singleLookup.history.headers.searched'),
      render: (search) => new Date(search.searched_at).toLocaleString(),
    },
  ];

  return (
    <HistoryTable
      columns={columns}
      fetchRows={lookupHistoryApi.listSearches}
      onDelete={lookupHistoryApi.deleteSearch}
      onRowClick={(search) => navigate(`/ioc-tools/lookup/history/${search.id}`)}
      emptyText={t('singleLookup.history.empty')}
      actionsLabel={t('singleLookup.history.headers.actions')}
    />
  );
}
