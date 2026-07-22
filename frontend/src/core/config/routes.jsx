import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAtomValue } from 'jotai';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Layout from '../components/layout/Layout';
import NotFound from "../components/ui/NotFound";
import ErrorBoundary from '../components/ErrorBoundary';
import StartScreen from '../components/ui/StartScreen';
import { generalSettingsState } from '../state/atoms';

const CvssCalculator = lazy(() => import("../../features/cvss-calculator/CvssCalculator"));
const EmailAnalyzer = lazy(() => import("../../features/email-analyzer/EmailAnalyzer"));
const ImageTools = lazy(() => import("../../features/image-tools/ImageTools"));
const IocTools = lazy(() => import("../../features/ioc-tools/IocTools"));
const Newsfeed = lazy(() => import("../../features/newsfeed/Newsfeed"));
const Settings = lazy(() => import("../../features/settings/Settings"));
const RuleCreator = lazy(() => import("../../features/rule-creator/RuleCreator"));
const AiTemplates = lazy(() => import("../../features/llm-templates/AiTemplates"));
const UsernameSearch = lazy(() => import("../../features/username-search/UsernameSearch"));
const EmailSearch = lazy(() => import("../../features/email-search/EmailSearch"));
const RedditSearch = lazy(() => import("../../features/reddit-search/RedditSearch"));
const DorkRunner = lazy(() => import("../../features/dork-runner/DorkRunner"));
const GitRecon = lazy(() => import("../../features/git-recon/GitRecon"));

const LoadingFallback = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
    <CircularProgress />
  </Box>
);

/** `startScreen` setting picks what `/` renders: the search home, or today's newsfeed default. */
const IndexRoute = () => {
  const generalSettings = useAtomValue(generalSettingsState);
  const startScreen = generalSettings?.start_screen ?? 'search';
  return startScreen === 'newsfeed' ? <Navigate to="/newsfeed" replace /> : <StartScreen />;
};

export const AppRoutes = () => {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<IndexRoute />} />
          <Route path="newsfeed/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><Newsfeed /></Suspense></ErrorBoundary>} />
          <Route path="settings/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><Settings /></Suspense></ErrorBoundary>} />
          <Route path="ai-templates/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><AiTemplates /></Suspense></ErrorBoundary>} />
          <Route path="ioc-tools/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><IocTools /></Suspense></ErrorBoundary>} />
          <Route path="email-analyzer/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><EmailAnalyzer /></Suspense></ErrorBoundary>} />
          <Route path="image-tools/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><ImageTools /></Suspense></ErrorBoundary>} />
          <Route path="cvss-calculator/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><CvssCalculator /></Suspense></ErrorBoundary>} />
          <Route path="rules/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><RuleCreator /></Suspense></ErrorBoundary>} />
          <Route path="username-search/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><UsernameSearch /></Suspense></ErrorBoundary>} />
          <Route path="email-search/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><EmailSearch /></Suspense></ErrorBoundary>} />
          <Route path="reddit-search/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><RedditSearch /></Suspense></ErrorBoundary>} />
          <Route path="dork-runner/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><DorkRunner /></Suspense></ErrorBoundary>} />
          <Route path="git-recon/*" element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><GitRecon /></Suspense></ErrorBoundary>} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
};
