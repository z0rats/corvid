import { Routes, Route, Navigate } from 'react-router';
import { useTranslation } from 'react-i18next';

import PageHeader from '../../core/components/ui/PageHeader';
import TemplatesView from './components/ui/TemplatesView';
import CreateTemplateForm from './components/forms/CreateTemplateForm';

export default function AiTemplates() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t('nav.aiTemplates')} />
      <Routes>
        <Route path="/" element={<Navigate to="/ai-templates/templates" replace />} />
        <Route path="templates" element={<TemplatesView />} />
        <Route path="create-template" element={<CreateTemplateForm />} />
      </Routes>
    </>
  );
}
