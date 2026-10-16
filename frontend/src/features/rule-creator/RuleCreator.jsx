import React from 'react';
import { Routes, Route, Navigate } from "react-router";
import Sigma from './sigma/Sigma';
import Yara from './yara/Yara';
import Snort from './snort/Snort';
import NotFound from '../../core/components/ui/NotFound';
import { useTranslation } from 'react-i18next';
import PageHeader from '../../core/components/ui/PageHeader';

export default function RuleCreator() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t('nav.detectionRules')} />
      <Routes>
        <Route path="/" element={<Navigate to="sigma" replace />} />
        <Route path="sigma" element={<Sigma />} />
        <Route path="yara" element={<Yara />} />
        <Route path="snort" element={<Snort />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}
