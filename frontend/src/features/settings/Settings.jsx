import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import NotFound from '../../core/components/ui/NotFound';

import AiSettings from './ai-settings/AiSettings';
import General from './general/General';
import About from './about/About';
import ApiKeys from './api-keys/ApiKeys';
import Modules from './modules/Modules';
import CommandPaletteSettings from './command-palette/CommandPaletteSettings';

/**
 * Settings feature router component
 */
export default function Settings() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="apikeys" replace />} />
      <Route path="apikeys" element={<ApiKeys />} />
      <Route path="modules" element={<Modules />} />
      <Route path="ai-settings" element={<AiSettings />} />
      <Route path="general" element={<General />} />
      <Route path="command-palette" element={<CommandPaletteSettings />} />
      <Route path="about" element={<About />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
