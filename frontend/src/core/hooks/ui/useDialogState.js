import { useState, useCallback } from 'react';

export function useDialogState() {
  const [open, setOpen] = useState(false);
  const [item, setItem] = useState(null);

  const openDialog = useCallback((dialogItem = null) => {
    setItem(dialogItem);
    setOpen(true);
  }, []);

  const closeDialog = useCallback(() => {
    setOpen(false);
    setItem(null);
  }, []);

  return { open, item, openDialog, closeDialog };
}
