import { useState, useCallback } from 'react';

export function useIocLookupDialog() {
  const [open, setOpen] = useState(false);
  const [ioc, setIoc] = useState(null);
  const [iocType, setIocType] = useState(null);

  const openDialog = useCallback((iocValue, type) => {
    setIoc(iocValue);
    setIocType(type);
    setOpen(true);
  }, []);

  const closeDialog = useCallback(() => {
    setOpen(false);
  }, []);

  return { open, ioc, iocType, openDialog, closeDialog };
}
