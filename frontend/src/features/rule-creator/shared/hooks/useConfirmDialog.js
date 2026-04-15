import { useState, useCallback } from 'react';

export function useConfirmDialog() {
  const [dialogState, setDialogState] = useState({
    open: false,
    title: '',
    message: '',
    onConfirm: null,
  });

  const requestConfirmation = useCallback((title, message, onConfirm) => {
    setDialogState({ open: true, title, message, onConfirm });
  }, []);

  const handleConfirm = useCallback(() => {
    dialogState.onConfirm?.();
    setDialogState(prev => ({ ...prev, open: false }));
  }, [dialogState]);

  const handleCancel = useCallback(() => {
    setDialogState(prev => ({ ...prev, open: false }));
  }, []);

  return {
    dialogState,
    requestConfirmation,
    handleConfirm,
    handleCancel,
  };
}
