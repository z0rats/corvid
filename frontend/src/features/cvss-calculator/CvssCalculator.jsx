import React from 'react';
import { useTranslation } from 'react-i18next';
import { Routes, Route, Navigate } from 'react-router';
import Cvss31Calculator from './cvss-3.1/Cvss31Calculator';
import Cvss40Calculator from './cvss-4.0/Cvss40Calculator';
import PageHeader from '../../core/components/ui/PageHeader';

/**
 * Main CVSS Calculator router component
 * Handles routing between different CVSS versions
 */
export default function CvssCalculator() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t('nav.cvssCalculator')} />
      <Routes>
        <Route index element={<Navigate to="cvss-3.1" replace />} />
        <Route path="cvss-3.1" element={<Cvss31Calculator />} />
        <Route path="cvss-4.0" element={<Cvss40Calculator />} />
      </Routes>
    </>
  );
}
