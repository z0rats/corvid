import { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router';
import { useAtomValue } from 'jotai';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Layout from '../components/layout/Layout';
import NotFound from "../components/ui/NotFound";
import ErrorBoundary from '../components/ErrorBoundary';
import StartScreen from '../components/ui/StartScreen';
import { generalSettingsState } from '../state/atoms';
import { FEATURE_ROUTES } from './featureRoutes';

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
          {FEATURE_ROUTES.map(({ path, Component }) => (
            <Route
              key={path}
              path={path}
              element={<ErrorBoundary><Suspense fallback={<LoadingFallback />}><Component /></Suspense></ErrorBoundary>}
            />
          ))}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
};
