import { Routes, Route } from 'react-router';
import { IdentityRedirect } from '../../core/hooks/usePrefillFromQuery';
import ProfileLookup from './components/ProfileLookup';
import NewScan from './components/NewScan';
import HistoryList from './components/HistoryList';
import HistoryDetail from './components/HistoryDetail';

// index -> "profile" (not "new", unlike Amass/GitRecon/SteamRecon's scan-first
// features) - the profile lookup was this feature's whole Phase 1, so existing
// bookmarks/command-palette pivots targeting the bare route should keep landing
// on it, not the newer followers/followees/posts scan.
export default function InstagramSearch() {
  return (
    <Routes>
      <Route index element={<IdentityRedirect to="profile" />} />
      <Route path="profile" element={<ProfileLookup />} />
      <Route path="new" element={<NewScan />} />
      <Route path="history" element={<HistoryList />} />
      <Route path="history/:id" element={<HistoryDetail />} />
    </Routes>
  );
}
