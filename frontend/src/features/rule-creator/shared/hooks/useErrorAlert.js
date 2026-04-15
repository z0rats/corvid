import { useState, useCallback } from 'react';

export function useErrorAlert() {
  const [errorAlert, setErrorAlert] = useState({ open: false, message: '' });

  const showError = useCallback((message) => {
    setErrorAlert({ open: true, message });
  }, []);

  const hideError = useCallback(() => {
    setErrorAlert({ open: false, message: '' });
  }, []);

  return { errorAlert, showError, hideError };
}
