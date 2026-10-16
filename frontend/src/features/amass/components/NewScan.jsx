import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import Button from '@mui/material/Button';
import CancelIcon from '@mui/icons-material/Cancel';

import ScanForm from './ScanForm';
import ResultsView from './ResultsView';
import { useAmass } from '../hooks/useAmass';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';
import ScanQueuedNotice from '../../../core/components/ui/ScanQueuedNotice';
import PageHeader from '../../../core/components/ui/PageHeader';

export default function NewScan() {
  const { t } = useTranslation('amass');
  const { result, loading, queued, error, scan, cancelScan } = useAmass();

  // Hand-off from a command-palette pivot (e.g. a domain sent to Amass) - see crossFeatureNav.ts.
  const prefillValue = usePrefillFromQuery(useCallback((value) => scan({
    domain: value,
    brute_force: false,
  }), [scan]));

  return (
    <Box>
      <PageHeader title={t('page.title')} description={t('page.description')} />

      <ScanForm onScan={scan} disabled={loading} initialTarget={prefillValue} />

      {loading && (
        <Box sx={{ mb: 2 }}>
          {queued && <ScanQueuedNotice />}
          <LinearProgress sx={{ mb: 0.5 }} />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button size="small" color="error" startIcon={<CancelIcon />} onClick={cancelScan}>
              {t('form.cancelButton')}
            </Button>
          </Box>
        </Box>
      )}
      {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}

      <ResultsView result={result?.result} />
    </Box>
  );
}
