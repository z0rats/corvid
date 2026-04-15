import { useState, useCallback, useMemo } from 'react';
import { defangApi } from '../../../shared/services/api/defangApi';
import { createFallbackResults } from '../../utils/defangerUtils';
import { createLogger } from '../../../../../core/utils/logger';

const logger = createLogger('Defanger');

export const useDefanger = () => {
  const [inputText, setInputText] = useState('');
  const [results, setResults] = useState([]);
  const [operation, setOperation] = useState('defang');
  const [showOnlyChanged, setShowOnlyChanged] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  const handleProcess = useCallback(async () => {
    if (!inputText.trim()) {
      setResults([]);
      return;
    }

    try {
      const processedResults = await defangApi.batchProcessIOCs(inputText, operation);
      setResults(processedResults);
    } catch (error) {
      logger.error('Error processing IOCs:', error);
      setResults(createFallbackResults(inputText));
    }
  }, [inputText, operation]);

  const handleCopy = useCallback((text, type = 'result') => {
    navigator.clipboard.writeText(text).then(() => {
      setSnackbar({ open: true, message: `${type} copied to clipboard!`, severity: 'success' });
    }).catch(() => {
      setSnackbar({ open: true, message: 'Failed to copy to clipboard', severity: 'error' });
    });
  }, []);

  const handleCopyAllResults = useCallback(() => {
    const filteredResults = showOnlyChanged ? results.filter(r => r.changed) : results;
    const allResults = filteredResults.map(r => r.processed).join('\n');
    handleCopy(allResults, 'All results');
  }, [results, showOnlyChanged, handleCopy]);

  const handleDownloadCsv = useCallback(() => {
    const filteredResults = showOnlyChanged ? results.filter(r => r.changed) : results;
    if (filteredResults.length === 0) {
      setSnackbar({ open: true, message: 'No results to download', severity: 'warning' });
      return;
    }

    const escape = (value) => {
      const str = String(value ?? '');
      return /[",\n\r]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str;
    };

    const processedHeader = operation === 'defang' ? 'Defanged' : 'Fanged';
    const header = ['Original', processedHeader, 'Type(s)', 'Status'];
    const rows = filteredResults.map(r => [
      r.original,
      r.processed,
      r.types.join('; '),
      r.changed ? 'Modified' : 'Unchanged',
    ]);
    const csv = [header, ...rows].map(row => row.map(escape).join(',')).join('\n');

    const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    link.href = url;
    link.download = `ioc-${operation}-results-${timestamp}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setSnackbar({ open: true, message: 'CSV downloaded', severity: 'success' });
  }, [results, showOnlyChanged, operation]);

  const handleSetOperation = useCallback(async (newOperation) => {
    if (!newOperation || newOperation === operation) return;
    setOperation(newOperation);

    if (results.length > 0) {
      try {
        const processedResults = await defangApi.batchProcessIOCs(inputText, newOperation);
        setResults(processedResults);
      } catch (error) {
        logger.error('Error re-processing IOCs:', error);
      }
    }
  }, [operation, inputText, results.length]);

  const handleClear = () => { setInputText(''); setResults([]); };

  const handleInputChange = (value) => setInputText(value);

  const handleToggleShowOnlyChanged = (checked) => setShowOnlyChanged(checked);

  const filteredResults = useMemo(
    () => showOnlyChanged ? results.filter(r => r.changed) : results,
    [results, showOnlyChanged]
  );

  const changedCount = useMemo(
    () => results.filter(r => r.changed).length,
    [results]
  );

  return {
    inputText,
    results,
    operation,
    showOnlyChanged,
    snackbar,
    closeSnackbar: () => setSnackbar({ ...snackbar, open: false }),
    handleProcess,
    handleCopy,
    handleCopyAllResults,
    handleDownloadCsv,
    handleSetOperation,
    handleClear,
    handleInputChange,
    handleToggleShowOnlyChanged,
    filteredResults,
    changedCount,
    hasResults: results.length > 0,
  };
};
