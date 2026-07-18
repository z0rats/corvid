import { useState, useCallback, useEffect } from 'react';
import { dorkRunnerApi } from '../../services/api/dorkRunnerApi';
import { usePrefillFromQuery } from '../../../../core/hooks/usePrefillFromQuery';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('DorkRunner');

export function useDorkRunner() {
  const [target, setTarget] = useState('');
  const [targetType, setTargetType] = useState('domain');
  const [engine, setEngine] = useState('duckduckgo');
  const [templates, setTemplates] = useState([]);
  const [selectedTemplateKeys, setSelectedTemplateKeys] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { prefillValue, clearPrefill } = usePrefillFromQuery();

  useEffect(() => {
    let ignore = false;
    dorkRunnerApi.getTemplates(targetType)
      .then((data) => {
        if (ignore) return;
        setTemplates(data);
        setSelectedTemplateKeys(data.map((template) => template.key));
      })
      .catch((err) => {
        logger.error('Failed to load dork templates:', err);
      });
    return () => { ignore = true; };
  }, [targetType]);

  const toggleTemplate = useCallback((key) => {
    setSelectedTemplateKeys((prev) => (
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    ));
  }, []);

  const runDorks = useCallback(async (targetOverride) => {
    const targetValue = (targetOverride ?? target).trim();
    if (!targetValue) return;

    setLoading(true);
    setError(null);
    try {
      const data = await dorkRunnerApi.runDorks({
        target: targetValue,
        targetType,
        engine,
        templateKeys: selectedTemplateKeys.length ? selectedTemplateKeys : undefined,
      });
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Dork run failed');
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [target, targetType, engine, selectedTemplateKeys]);

  useEffect(() => {
    if (!prefillValue) return;
    setTarget(prefillValue);
    runDorks(prefillValue);
    clearPrefill();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillValue]);

  return {
    target,
    setTarget,
    targetType,
    setTargetType,
    engine,
    setEngine,
    templates,
    selectedTemplateKeys,
    toggleTemplate,
    result,
    loading,
    error,
    runDorks,
  };
}
