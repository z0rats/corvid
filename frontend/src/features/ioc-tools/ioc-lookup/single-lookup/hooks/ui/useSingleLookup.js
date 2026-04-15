import { useState, useRef, useCallback } from 'react';
import { determineIocType } from '../../../shared/utils/iocDefinitions';

export function useSingleLookup() {
  const [searchValue, setSearchValue] = useState('');
  const [currentIocType, setCurrentIocType] = useState('');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [shouldShowTable, setShouldShowTable] = useState(false);
  const inputRef = useRef(null);

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

  return {
    searchValue,
    currentIocType,
    snackbarOpen,
    shouldShowTable,
    inputRef,
    handleSubmitSearch,
    handleKeyPress,
    handleCloseError,
  };
}
