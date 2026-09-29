import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';

import HistoryTable from '../../../core/components/HistoryTable';
import { steamReconApi } from '../services/api/steamReconApi';
import ScanStatusChip from '../../../core/components/ScanStatusChip';


export default function HistoryList() {
  const { t } = useTranslation('steamRecon');
  const navigate = useNavigate();

  const columns = [
    {
      key: 'target',
      header: t('history.headers.target'),
      render: (search) => search.persona_name || search.target,
    },
    {
      key: 'status',
      header: t('history.headers.status'),
      render: (search) => (
        <ScanStatusChip status={search.status} label={t(`history.status.${search.status}`)} />
      ),
    },
    {
      key: 'friends',
      header: t('history.headers.friends'),
      render: (search) => `${search.friends_analyzed}/${search.friends_total}`,
    },
    {
      key: 'cheater_probability',
      header: t('history.headers.cheaterProbability'),
      render: (search) =>
        search.cheater_probability == null ? '-' : `${(search.cheater_probability * 100).toFixed(0)}%`,
    },
    {
      key: 'started_at',
      header: t('history.headers.started'),
      render: (search) => new Date(search.started_at).toLocaleString(),
    },
  ];

  return (
    <HistoryTable
      columns={columns}
      fetchRows={steamReconApi.listSearches}
      onDelete={steamReconApi.deleteSearch}
      onRowClick={(search) => navigate(`/steam-recon/history/${search.id}`)}
      emptyText={t('history.empty')}
      actionsLabel={t('history.headers.actions')}
    />
  );
}
