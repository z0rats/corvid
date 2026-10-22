import { Routes, Route } from 'react-router';
import InvestigationList from './components/InvestigationList';
import InvestigationDetail from './components/InvestigationDetail';

export default function Investigations() {
  return (
    <Routes>
      <Route index element={<InvestigationList />} />
      <Route path=":id" element={<InvestigationDetail />} />
    </Routes>
  );
}
