import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { determineIocType } from '../../../shared/utils/iocDefinitions';
import { lookupHistoryApi } from '../../services/api/lookupHistoryApi';
import { createLogger } from '../../../../../../core/utils/logger';
import { useUrlQuery } from '../../../../../../core/hooks/useUrlQuery';
import { refang } from '../../../../../../core/utils/refang';

const logger = createLogger('SingleLookupHistory');

/**
 * The looked-up IOC lives in the URL (`?q=`), so a lookup survives reload/Back and can be
 * bookmarked; revisits are served from the session cache in useServiceFetcher rather than
 * re-querying every provider. Re-submitting the value already shown is an explicit refresh.
 */
export function useSingleLookup() {
  const [urlValue, setUrlValue] = useUrlQuery();
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  // Bumped by re-submitting the current value: remounts the result table and bypasses the cache.
  const [refresh, setRefresh] = useState({ value: null, count: 0 });
  const inputRef = useRef(null);

  const searchValue = useMemo(() => refang(urlValue), [urlValue]);
  const detectedType = useMemo(() => (searchValue ? determineIocType(searchValue) : ''), [searchValue]);
  const isValid = Boolean(detectedType) && detectedType !== 'unknown';

  useEffect(() => {
    if (inputRef.current && inputRef.current.value !== searchValue) {
      inputRef.current.value = searchValue;
    }
    // An unrecognized value arriving via the URL (pivot, bookmark) gets the same feedback as a typed one.
    if (searchValue && !isValid) setSnackbarOpen(true);
  }, [searchValue, isValid]);

  const handleValidation = useCallback((iocInput) => {
    const value = refang(iocInput);

    if (!value) {
      setSnackbarOpen(false);
      setUrlValue('');
      return false;
    }

    if (determineIocType(value) === 'unknown') {
      setSnackbarOpen(true);
      return false;
    }

    setSnackbarOpen(false);
    if (inputRef.current && inputRef.current.value !== value) {
      inputRef.current.value = value;
    }
    if (value === searchValue) {
      setRefresh((prev) => ({ value, count: prev.value === value ? prev.count + 1 : 1 }));
    } else {
      setUrlValue(value);
    }
    return true;
  }, [searchValue, setUrlValue]);

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

  const refreshCount = refresh.value === searchValue ? refresh.count : 0;

  return {
    searchValue: isValid ? searchValue : '',
    currentIocType: isValid ? detectedType : '',
    snackbarOpen,
    shouldShowTable: isValid,
    refreshKey: `${searchValue}#${refreshCount}`,
    bypassCache: refreshCount > 0,
    inputRef,
    handleSubmitSearch,
    handleKeyPress,
    handleCloseError,
    handleSearchComplete,
  };
}
