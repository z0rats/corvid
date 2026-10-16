import React from 'react';
import { useTranslation } from 'react-i18next';
import { Routes, Route, Navigate } from 'react-router';
import SingleLookup from './ioc-lookup/single-lookup/SingleLookup';
import HistoryList from './ioc-lookup/single-lookup/components/history/HistoryList';
import HistoryDetail from './ioc-lookup/single-lookup/components/history/HistoryDetail';
import BulkLookup from './ioc-lookup/bulk-lookup/BulkLookup';
import IocExtractor from './ioc-extractor/IocExtractor';
import IocDefanger from './ioc-defanger/IocDefanger';
import DomainFinder from './domain-finder/DomainMonitoring';
import PageHeader from '../../core/components/ui/PageHeader';

// One feature-level title above every tab, like CVSS/Rules/Newsfeed: a per-tab title would only
// repeat the highlighted tab's own label right above it.
const IocTools = () => {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t('nav.iocTools')} />
      <Routes>
        <Route index element={<Navigate to="lookup" replace />} />
        <Route path="lookup" element={<SingleLookup />} />
        <Route path="lookup/history" element={<HistoryList />} />
        <Route path="lookup/history/:id" element={<HistoryDetail />} />
        <Route path="bulk/*" element={<BulkLookup />} />
        <Route path="domain-finder" element={<DomainFinder />} />
        <Route path="extractor" element={<IocExtractor />} />
        <Route path="defanger" element={<IocDefanger />} />
      </Routes>
    </>
  );
};

export default IocTools;
