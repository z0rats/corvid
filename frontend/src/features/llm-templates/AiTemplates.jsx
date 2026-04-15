import { Routes, Route, Navigate } from 'react-router-dom';

import TemplatesView from './components/ui/TemplatesView';
import CreateTemplateForm from './components/forms/CreateTemplateForm';

export default function AiTemplates() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/ai-templates/templates" replace />} />
      <Route path="templates" element={<TemplatesView />} />
      <Route path="create-template" element={<CreateTemplateForm />} />
    </Routes>
  );
}
