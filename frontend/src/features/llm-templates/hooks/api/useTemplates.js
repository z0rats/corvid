import { useState, useCallback, useEffect } from 'react';

import { templatesApi } from '../../services/api/templatesApi';
import { extractErrorMessage } from '../../../../core/utils/errorUtils';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('Templates');

export function useTemplates() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTemplates = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await templatesApi.getTemplates();
      setTemplates(Array.isArray(data) ? data : []);
    } catch (err) {
      logger.error('Failed to fetch templates:', err);
      setError(extractErrorMessage(err));
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const reorderTemplates = useCallback(async (sourceIndex, destinationIndex) => {
    const items = Array.from(templates);
    const [moved] = items.splice(sourceIndex, 1);
    items.splice(destinationIndex, 0, moved);
    setTemplates(items);

    try {
      await templatesApi.reorderTemplates(items.map(t => t.id));
    } catch (err) {
      logger.error('Failed to reorder templates:', err);
      fetchTemplates();
    }
  }, [templates, fetchTemplates]);

  const deleteTemplate = useCallback(async (templateId) => {
    try {
      await templatesApi.deleteTemplate(templateId);
      setTemplates(prev => prev.filter(t => t.id !== templateId));
    } catch (err) {
      logger.error('Failed to delete template:', err);
      throw err;
    }
  }, []);

  return {
    templates,
    setTemplates,
    loading,
    error,
    fetchTemplates,
    reorderTemplates,
    deleteTemplate,
  };
}
