import React, { useState, useCallback } from 'react';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Grid from '@mui/material/Grid';

import { useWordFrequency } from '../hooks/api/useTrendsApi';
import { useArticlesByIds } from '../hooks/api/useNewsfeedApi';
import { useTrendsBlacklist } from '../hooks/api/useTrendsBlacklistApi';
import { useNotification } from '../../../core/hooks/ui/useNotification';

import TrendsHeader from './components/TrendsHeader';
import WordFrequencyChart from './components/WordFrequencyChart';
import IocStatistics from './components/IocStatistics';
import CveStatistics from './components/CveStatistics';
import IocDistributionChart from './components/IocDistributionChart';
import ArticleTable from './components/ArticleTable';
import NotificationSnackbar from '../components/ui/NotificationSnackbar';

export default function Trends() {
  const [selectedArticleIds, setSelectedArticleIds] = useState([]);
  const [selectedTitle, setSelectedTitle] = useState(null);
  const [timeRange, setTimeRange] = useState('7d');
  const [refreshKey, setRefreshKey] = useState(0);

  const { data: wordFrequencyData, loading: loadingWordFrequency, error: errorWordFrequency } = useWordFrequency(timeRange, refreshKey);
  const { articleDetails, articleLoading, fetchArticleDetails, clearArticleDetails } = useArticlesByIds();
  const { addToBlacklist } = useTrendsBlacklist();
  const { notification, showSuccess, showError, hideNotification } = useNotification();

  const handleSelectArticleIds = useCallback((articleIds, title) => {
    setSelectedArticleIds(Array.isArray(articleIds) ? articleIds : []);
    setSelectedTitle(title);
    clearArticleDetails();

    if (Array.isArray(articleIds) && articleIds.length > 0) {
      fetchArticleDetails(articleIds);
    }
  }, [fetchArticleDetails, clearArticleDetails]);

  const handleRefresh = useCallback(() => {
    setRefreshKey(prev => prev + 1);
    setSelectedArticleIds([]);
    setSelectedTitle(null);
    clearArticleDetails();
  }, [clearArticleDetails]);

  const handleTimeRangeChange = useCallback((event) => {
    setTimeRange(event.target.value);
    setSelectedArticleIds([]);
    setSelectedTitle(null);
    clearArticleDetails();
  }, [clearArticleDetails]);

  const handleBlacklistWord = useCallback(async (word) => {
    const result = await addToBlacklist(word, 'word');
    if (result.success) {
      showSuccess(`"${word}" added to blacklist`);
      setRefreshKey(prev => prev + 1);
    } else if (result.duplicate) {
      showError(`"${word}" is already blacklisted`);
    } else {
      showError('Failed to blacklist word');
    }
  }, [addToBlacklist, showSuccess, showError]);

  const handleBlacklistIoc = useCallback(async (iocValue) => {
    const result = await addToBlacklist(iocValue, 'ioc');
    if (result.success) {
      showSuccess(`"${iocValue}" added to blacklist`);
      setRefreshKey(prev => prev + 1);
    } else if (result.duplicate) {
      showError(`"${iocValue}" is already blacklisted`);
    } else {
      showError('Failed to blacklist IOC');
    }
  }, [addToBlacklist, showSuccess, showError]);

  if (loadingWordFrequency) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <TrendsHeader
        timeRange={timeRange}
        onTimeRangeChange={handleTimeRangeChange}
        onRefresh={handleRefresh}
      />

      <Grid container spacing={2} alignItems="stretch">
        {/* First Row: Word Frequency Chart (left) and Top CVEs (right) */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <WordFrequencyChart
              data={wordFrequencyData}
              loading={loadingWordFrequency}
              error={errorWordFrequency}
              onSelectArticleIds={handleSelectArticleIds}
              onBlacklistWord={handleBlacklistWord}
            />
          </Box>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CveStatistics
              timeRange={timeRange}
              refreshKey={refreshKey}
              onSelectArticleIds={handleSelectArticleIds}
            />
          </Box>
        </Grid>

        {/* Second Row: Top IOCs (left) and IOC Distribution Chart (right) */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <IocStatistics
              timeRange={timeRange}
              refreshKey={refreshKey}
              onSelectArticleIds={handleSelectArticleIds}
              onBlacklistIoc={handleBlacklistIoc}
            />
          </Box>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <IocDistributionChart
              timeRange={timeRange}
              refreshKey={refreshKey}
            />
          </Box>
        </Grid>
      </Grid>

      <ArticleTable
        selectedArticleIds={selectedArticleIds}
        selectedTitle={selectedTitle}
        articleDetails={articleDetails}
        articleLoading={articleLoading}
      />

      <NotificationSnackbar
        open={notification.open}
        message={notification.message}
        severity={notification.severity}
        onClose={hideNotification}
      />
    </Box>
  );
}
