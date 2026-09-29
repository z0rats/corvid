import { Routes, Route } from 'react-router';
import { IdentityRedirect } from '../../core/hooks/usePrefillFromQuery';
import NewScan from './components/NewScan';
import HistoryList from './components/HistoryList';
import HistoryDetail from './components/HistoryDetail';

export default function Amass() {
  return (
    <Routes>
      <Route index element={<IdentityRedirect to="new" />} />
      <Route path="new" element={<NewScan />} />
      <Route path="history" element={<HistoryList />} />
      <Route path="history/:id" element={<HistoryDetail />} />
    </Routes>
  );
}
