import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import HistoryTable from '../../../core/components/HistoryTable';
import { redditSearchApi } from '../services/api/redditSearchApi';

export default function HistoryList() {
  const { t } = useTranslation('redditSearch');
  const navigate = useNavigate();

  const columns = [
    { key: 'username', header: t('history.headers.username') },
    { key: 'result_count', header: t('history.headers.results') },
    {
      key: 'searched_at',
      header: t('history.headers.searched'),
      render: (search) => new Date(search.searched_at).toLocaleString(),
    },
  ];

  return (
    <HistoryTable
      columns={columns}
      fetchRows={redditSearchApi.listHistory}
      onDelete={redditSearchApi.deleteHistory}
      onRowClick={(search) => navigate(`/reddit-search/history/${search.id}`)}
      emptyText={t('history.empty')}
      actionsLabel={t('history.headers.actions')}
    />
  );
}
