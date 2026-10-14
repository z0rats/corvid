import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';

/** Shown while a heavy scan waits for a free backend slot (`queued` from useResumableScan). */
export default function ScanQueuedNotice() {
  const { t } = useTranslation('common');
  return (
    <Alert severity="info" sx={{ mb: 1 }}>
      {t('scanQueue.waiting')}
    </Alert>
  );
}
