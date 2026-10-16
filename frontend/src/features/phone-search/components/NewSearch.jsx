import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';

import SearchForm from './SearchForm';
import LiveScanView from './LiveScanView';
import ToolInfoBanner from './ToolInfoBanner';
import { usePhoneSearchScan } from '../hooks/usePhoneSearchScan';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';
import PageHeader from '../../../core/components/ui/PageHeader';

export default function NewSearch() {
  const { t } = useTranslation('phoneSearch');
  const scan = usePhoneSearchScan();
  // Hand-off from a command-palette pivot (e.g. "+15551234567 phone") — see crossFeatureNav.ts.
  const prefillValue = usePrefillFromQuery(useCallback((value) => scan.startScan(value), [scan]));

  return (
    <Box>
      <PageHeader title={t('page.title')} description={t('page.description')} />
      <ToolInfoBanner />
      <SearchForm onSearch={scan.startScan} disabled={scan.phase === 'running'} initialPhoneNumber={prefillValue} />
      {scan.phase !== 'idle' && <LiveScanView scan={scan} />}
    </Box>
  );
}
