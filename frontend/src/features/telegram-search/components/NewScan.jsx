import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';

import ScanForm from './ScanForm';
import LiveScanView from './LiveScanView';
import ChannelReport from './ChannelReport';
import { useTelegramScan } from '../hooks/useTelegramScan';
import { MAX_POSTS_DEFAULT } from '../utils/telegramSearchConfig';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';
import PageHeader from '../../../core/components/ui/PageHeader';

export default function NewScan() {
  const { t } = useTranslation('telegramSearch');
  const { t: tCommon } = useTranslation();
  const scan = useTelegramScan();

  // Command-palette pivot or a channel chip from another scan's report (see crossFeatureNav.ts).
  const prefillValue = usePrefillFromQuery(
    useCallback((value) => scan.startScan(value, { maxPosts: MAX_POSTS_DEFAULT }), [scan]),
  );
  const running = scan.phase === 'running';

  return (
    <Box>
      <PageHeader title={tCommon('nav.telegramSearch')} description={t('page.description')} />

      {/* Keyed by the scanned target so a pivot from a report chip refills the field. */}
      <ScanForm
        key={scan.target}
        onSubmit={scan.startScan}
        disabled={running}
        initialTarget={scan.target || prefillValue}
      />

      {scan.phase !== 'idle' && <LiveScanView scan={scan} cancelScan={scan.cancelScan} />}

      <ChannelReport result={scan.result?.result} disabled={running} />
    </Box>
  );
}
