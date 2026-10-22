import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';

import HistoryTable from '../../../core/components/HistoryTable';
import ScanStatusChip from '../../../core/components/ScanStatusChip';
import { telegramSearchApi } from '../services/api/telegramSearchApi';
import { formatCompact } from '../utils/telegramFormat';

export default function HistoryList() {
  const { t: tCommon } = useTranslation();
  const { t } = useTranslation('telegramSearch');
  const navigate = useNavigate();

  const columns = [
    {
      key: 'channel',
      header: t('history.headers.channel'),
      render: (search) => (search.title ? `${search.title} (@${search.channel})` : `@${search.channel}`),
    },
    {
      key: 'status',
      header: t('history.headers.status'),
      render: (search) => (
        <ScanStatusChip status={search.status} label={t(`history.status.${search.status}`)} />
      ),
    },
    {
      key: 'member_count',
      header: t('history.headers.members'),
      render: (search) => formatCompact(search.member_count) ?? '-',
    },
    { key: 'posts_sampled', header: t('history.headers.posts') },
    {
      key: 'started_at',
      header: t('history.headers.started'),
      render: (search) => new Date(search.started_at).toLocaleString(),
    },
  ];

  return (
    <HistoryTable
      title={tCommon('nav.telegramSearch')}
      columns={columns}
      fetchRows={telegramSearchApi.listSearches}
      onDelete={telegramSearchApi.deleteSearch}
      onRowClick={(search) => navigate(`/telegram-search/history/${search.id}`)}
      emptyText={t('history.empty')}
      actionsLabel={t('history.headers.actions')}
    />
  );
}
