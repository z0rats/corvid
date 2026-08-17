import { useNavigate } from 'react-router';
import Chip from '@mui/material/Chip';

import HistoryTable from '../../../core/components/HistoryTable';
import { ruBusinessCheckApi } from '../services/api/ruBusinessCheckApi';

const STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };
const STATUS_LABELS = { running: 'Выполняется', completed: 'Завершено', cancelled: 'Отменено', failed: 'Ошибка' };
const RISK_LABELS = { low: 'Низкий', medium: 'Средний', high: 'Высокий' };
const RISK_COLORS = { low: 'success', medium: 'warning', high: 'error' };

export default function HistoryList() {
  const navigate = useNavigate();

  const columns = [
    { key: 'query', header: 'Запрос' },
    { key: 'resolved_inn', header: 'ИНН', render: (s) => s.resolved_inn || '—' },
    {
      key: 'status',
      header: 'Статус',
      render: (s) => <Chip size="small" label={STATUS_LABELS[s.status] || s.status} color={STATUS_COLORS[s.status] || 'default'} />,
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
