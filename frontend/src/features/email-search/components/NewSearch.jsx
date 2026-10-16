import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';

import SearchForm from './SearchForm';
import LiveScanView from './LiveScanView';
import ToolInfoBanner from './ToolInfoBanner';
import GhuntProfilePanel from './GhuntProfilePanel';
import { useEmailSearchScan } from '../hooks/useEmailSearchScan';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';
import PageHeader from '../../../core/components/ui/PageHeader';

export default function NewSearch() {
  const { t } = useTranslation('emailSearch');
  const scan = useEmailSearchScan();
  // The scan lives in a global atom and outlives this page; the selected tool must follow it,
  // or coming back to a finished User Scanner run would show the Mailcat form over its results.
  const [source, setSource] = useState(() => (scan.phase !== 'idle' ? scan.source : 'mailcat'));
  useEffect(() => {
    if (scan.phase !== 'idle') setSource(scan.source);
  }, [scan.phase, scan.source, scan.searchId]);
  const [ghuntPrefill, setGhuntPrefill] = useState(null);
  const lookupGoogleProfile = useCallback(
    (email) => setGhuntPrefill((prev) => ({ email, seq: (prev?.seq ?? 0) + 1 })),
    [],
  );
  // Hand-off from a command-palette pivot (e.g. "john_doe email") — see crossFeatureNav.ts.
  // Always mailcat, even for a full address: the pivot starts the scan right away, and
  // User Scanner (an address sent to ~150 services) must stay an explicit choice.
  const prefillValue = usePrefillFromQuery(useCallback((value) => scan.startScan(value), [scan]));

  return (
    <Box>
      <PageHeader title={t('page.title')} description={t('page.description')} />
      <ToolInfoBanner source={source} />
      <SearchForm
        onSearch={scan.startScan}
        disabled={scan.phase === 'running'}
        initialUsername={prefillValue}
        source={source}
        onSourceChange={setSource}
      />
      {source === 'user_scanner' && (
        <Alert severity="warning" sx={{ mb: 2 }}>{t('form.source.user_scanner.caveat')}</Alert>
      )}
      {scan.phase !== 'idle' && <LiveScanView scan={scan} onLookupGoogleProfile={lookupGoogleProfile} />}
      <GhuntProfilePanel prefill={ghuntPrefill} />
    </Box>
  );
}
