import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import SearchForm from './SearchForm';
import LiveScanView from './LiveScanView';
import ToolInfoBanner from './ToolInfoBanner';
import { usePhoneSearchScan } from '../hooks/usePhoneSearchScan';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';

export default function NewSearch() {
  const { t } = useTranslation('phoneSearch');
  const scan = usePhoneSearchScan();
  // Hand-off from a command-palette pivot (e.g. "+15551234567 phone") — see crossFeatureNav.ts.
  const prefillValue = usePrefillFromQuery(useCallback((value) => scan.startScan(value), [scan]));

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 1 }}>{t('page.title')}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('page.description')}
      </Typography>
      <ToolInfoBanner />
      <SearchForm onSearch={scan.startScan} disabled={scan.phase === 'running'} initialPhoneNumber={prefillValue} />
      {scan.phase !== 'idle' && <LiveScanView scan={scan} />}
    </Box>
  );
}
