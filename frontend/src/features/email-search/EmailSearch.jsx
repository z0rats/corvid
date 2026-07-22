import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import NewSearch from './components/NewSearch';
import HistoryList from './components/HistoryList';
import HistoryDetail from './components/HistoryDetail';
import Settings from './settings/Settings';

export default function EmailSearch() {
  // Carries the search string (e.g. a pivot's ?q=) through to "new" — a bare `to="new"` drops it,
  // since it only specifies a pathname.
  const location = useLocation();

  return (
    <Routes>
      <Route index element={<Navigate to={{ pathname: 'new', search: location.search }} replace />} />
      <Route path="new" element={<NewSearch />} />
      <Route path="history" element={<HistoryList />} />
      <Route path="history/:id" element={<HistoryDetail />} />
      <Route path="settings" element={<Settings />} />
    </Routes>
  );
}
