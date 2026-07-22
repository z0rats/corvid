import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import SearchForm from './SearchForm';
import LiveScanView from './LiveScanView';
import ToolInfoBanner from './ToolInfoBanner';
import { useUsernameSearchScan } from '../hooks/useUsernameSearchScan';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';

export default function NewSearch() {
  const { t } = useTranslation('usernameSearch');
  const scan = useUsernameSearchScan();
  const { prefillValue, clearPrefill } = usePrefillFromQuery();

  useEffect(() => {
    // Hand-off from a command-palette pivot (e.g. "john_doe username") — see crossFeatureNav.js.
    if (!prefillValue) return;
    scan.startScan(prefillValue);
    clearPrefill();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillValue]);

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 1 }}>{t('page.title')}</Typography>
      <ToolInfoBanner />
      <SearchForm onSearch={scan.startScan} disabled={scan.phase === 'running'} initialUsername={prefillValue} />
      {scan.phase !== 'idle' && <LiveScanView scan={scan} />}
    </Box>
  );
}
