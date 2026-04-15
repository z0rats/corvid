import { useState, useCallback } from 'react';

import { templatesApi } from '../../services/api/templatesApi';

export function useTemplateExecution() {
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState('');

  const executeTemplate = useCallback(async (template, payload) => {
    setExecuting(true);
    setResult('');

    try {
      const execPayload = {
        template_id: template.id,
        payload_data: payload,
      };
      if (template.model) execPayload.override_model = template.model;
      if (template.temperature !== undefined) execPayload.override_temperature = template.temperature;

      const data = await templatesApi.executeTemplate(template.id, execPayload);
      setResult(data.result || '');
      return data;
    } finally {
      setExecuting(false);
    }
  }, []);

  const clearResult = useCallback(() => setResult(''), []);

  return { executing, result, executeTemplate, clearResult };
}
