import React from 'react';
import { Routes, Route, Navigate } from "react-router-dom";
import Sigma from './sigma/Sigma';
import Yara from './yara/Yara';
import Snort from './snort/Snort';
import NotFound from '../../core/components/ui/NotFound';

export default function RuleCreator() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="sigma" replace />} />
      <Route path="sigma" element={<Sigma />} />
      <Route path="yara" element={<Yara />} />
      <Route path="snort" element={<Snort />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
