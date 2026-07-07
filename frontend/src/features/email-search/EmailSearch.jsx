import { Routes, Route, Navigate } from 'react-router-dom';
import NewSearch from './components/NewSearch';
import HistoryList from './components/HistoryList';
import HistoryDetail from './components/HistoryDetail';
import Settings from './settings/Settings';

export default function EmailSearch() {
  return (
    <Routes>
      <Route index element={<Navigate to="new" replace />} />
      <Route path="new" element={<NewSearch />} />
      <Route path="history" element={<HistoryList />} />
      <Route path="history/:id" element={<HistoryDetail />} />
      <Route path="settings" element={<Settings />} />
    </Routes>
  );
}
