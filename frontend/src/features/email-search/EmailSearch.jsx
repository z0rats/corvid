import { Routes, Route } from 'react-router';
import { IdentityRedirect } from '../../core/hooks/usePrefillFromQuery';
import NewSearch from './components/NewSearch';
import HistoryList from './components/HistoryList';
import HistoryDetail from './components/HistoryDetail';
import Settings from './settings/Settings';

export default function EmailSearch() {
  return (
    <Routes>
      <Route index element={<IdentityRedirect to="new" />} />
      <Route path="new" element={<NewSearch />} />
      <Route path="history" element={<HistoryList />} />
      <Route path="history/:id" element={<HistoryDetail />} />
      <Route path="settings" element={<Settings />} />
    </Routes>
  );
}
