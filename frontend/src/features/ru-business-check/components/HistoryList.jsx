import { useNavigate } from 'react-router';
import Chip from '@mui/material/Chip';

import HistoryTable from '../../../core/components/HistoryTable';
import { ruBusinessCheckApi } from '../services/api/ruBusinessCheckApi';
import { RISK_LABELS, RISK_COLORS } from '../constants/risk';
import ScanStatusChip from '../../../core/components/ScanStatusChip';

const STATUS_LABELS = { running: 'Выполняется', completed: 'Завершено', cancelled: 'Отменено', failed: 'Ошибка' };

export default function HistoryList() {
  const navigate = useNavigate();

  const columns = [
    { key: 'query', header: 'Запрос' },
    { key: 'resolved_inn', header: 'ИНН', render: (s) => s.resolved_inn || '—' },
    {
      key: 'status',
      header: 'Статус',
      render: (s) => <ScanStatusChip status={s.status} label={STATUS_LABELS[s.status] || s.status} />,
    },
    {
      key: 'risk_level',
      header: 'Риск',
      render: (s) => (s.risk_level ? <Chip size="small" label={RISK_LABELS[s.risk_level] || s.risk_level} color={RISK_COLORS[s.risk_level] || 'default'} /> : '—'),
    },
    {
      key: 'searched_at',
      header: 'Дата проверки',
      render: (s) => new Date(s.searched_at).toLocaleString(),
    },
  ];

  return (
    <HistoryTable
      columns={columns}
      fetchRows={ruBusinessCheckApi.listHistory}
      onDelete={ruBusinessCheckApi.deleteHistory}
      onRowClick={(search) => navigate(`/ru-business-check/history/${search.id}`)}
      emptyText="Пока нет ни одной проверки"
      actionsLabel="Действия"
    />
  );
}
