import { useTranslation } from 'react-i18next';

import HistoryTable from '../../../../core/components/HistoryTable';
import { geolocationHistoryApi } from '../../services/api/geolocationHistoryApi';

export default function GeolocationHistoryList({ onSelect }) {
  const { t } = useTranslation('imageTools');

  const columns = [
    { key: 'filename', header: t('geolocation.history.headers.filename') },
    {
      key: 'top_candidate',
      header: t('geolocation.history.headers.topCandidate'),
      render: (search) =>
        search.top_candidate
          ? `${search.top_candidate} (${Math.round((search.top_confidence ?? 0) * 100)}%)`
          : '—',
    },
    {
      key: 'searched_at',
      header: t('geolocation.history.headers.searched'),
      render: (search) => new Date(search.searched_at).toLocaleString(),
    },
  ];

  return (
    <HistoryTable
      columns={columns}
      fetchRows={geolocationHistoryApi.listSearches}
      onDelete={geolocationHistoryApi.deleteSearch}
      onRowClick={onSelect}
      emptyText={t('geolocation.history.empty')}
      actionsLabel={t('geolocation.history.headers.actions')}
    />
  );
}
