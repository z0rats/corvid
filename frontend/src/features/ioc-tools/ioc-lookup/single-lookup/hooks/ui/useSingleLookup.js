import { useState, useRef, useCallback, useEffect } from 'react';
import { determineIocType } from '../../../shared/utils/iocDefinitions';
import { lookupHistoryApi } from '../../services/api/lookupHistoryApi';
import { createLogger } from '../../../../../../core/utils/logger';
import { usePrefillFromQuery } from '../../../../../../core/hooks/usePrefillFromQuery';

const logger = createLogger('SingleLookupHistory');

export function useSingleLookup() {
  const [searchValue, setSearchValue] = useState('');
  const [currentIocType, setCurrentIocType] = useState('');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [shouldShowTable, setShouldShowTable] = useState(false);
  const inputRef = useRef(null);
  const { prefillValue, clearPrefill } = usePrefillFromQuery();

  const handleValidation = useCallback((iocInput) => {
    const trimmedIoc = iocInput.trim();

    if (!trimmedIoc) {
      setShouldShowTable(false);
      setSnackbarOpen(false);
      setSearchValue('');
      setCurrentIocType('');
      return false;
    }

    const type = determineIocType(trimmedIoc);

    if (type !== 'unknown') {
      setSnackbarOpen(false);
      setSearchValue(trimmedIoc);
      setCurrentIocType(type);
      setShouldShowTable(true);
      return true;
    } else {
      setShouldShowTable(false);
      setSnackbarOpen(true);
      return false;
    }
  }, []);

  const handleSubmitSearch = useCallback(() => {
    const inputValue = inputRef.current?.value || '';
    handleValidation(inputValue);
  }, [handleValidation]);

  const handleKeyPress = useCallback((event) => {
    if (event.key === 'Enter') {
      handleSubmitSearch();
    }
  }, [handleSubmitSearch]);

  const handleCloseError = useCallback(() => {
    setSnackbarOpen(false);
  }, []);

  const handleSearchComplete = useCallback(({ ioc, iocType, results }) => {
    lookupHistoryApi.saveSearch(ioc, iocType, results).catch((err) => {
      logger.error('Failed to save search to history:', err);
    });
  }, []);

  useEffect(() => {
    if (!prefillValue) return;
    if (inputRef.current) {
      inputRef.current.value = prefillValue;
    }
    handleValidation(prefillValue);
    clearPrefill();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillValue]);

  return {
    searchValue,
    currentIocType,
    snackbarOpen,
    shouldShowTable,
    inputRef,
    handleSubmitSearch,
    handleKeyPress,
    handleCloseError,
    handleSearchComplete,
  };
}
