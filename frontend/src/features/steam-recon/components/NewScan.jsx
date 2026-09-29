import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import ScanForm from './ScanForm';
import LiveScanView from './LiveScanView';
import CloseFriendsTable from './CloseFriendsTable';
import GeolocationCard from './GeolocationCard';
import CheaterReportCard from './CheaterReportCard';
import FriendGraphSvg from './FriendGraphSvg';
import { useSteamReconScan } from '../hooks/useSteamReconScan';
import { MAX_FRIENDS_DEFAULT } from '../utils/steamReconConfig';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';

export default function NewScan() {
  const { t } = useTranslation('steamRecon');
  const scan = useSteamReconScan();

  // Hand-off from a command-palette pivot (e.g. sending a SteamID here) - see crossFeatureNav.ts.
  const prefillValue = usePrefillFromQuery(
    useCallback(
      (value) => scan.startScan(value, { maxFriends: MAX_FRIENDS_DEFAULT, includeCsReport: true }),
      [scan],
    ),
  );

  // `scan.result` is the persisted SearchDetail record (see useSteamReconScan's reduce) - its own
  // `.result` field is the actual ScanResult blob (profile/close_friends/geolocation/...).
  const search = scan.result;
  const scanResult = search?.result;

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 1 }}>
        {t('scan.pageTitle')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('scan.pageDescription')}
      </Typography>

      <ScanForm onSubmit={scan.startScan} disabled={scan.phase === 'running'} initialTarget={prefillValue} />

      {scan.phase !== 'idle' && <LiveScanView scan={scan} cancelScan={scan.cancelScan} />}

      {scanResult && (
        <>
          <FriendGraphSvg closeFriends={scanResult.close_friends} targetLabel={scanResult.profile.persona_name} />
          <GeolocationCard geolocation={scanResult.geolocation} />
          <CloseFriendsTable closeFriends={scanResult.close_friends} />
          {scanResult.cheater_report && <CheaterReportCard cheaterReport={scanResult.cheater_report} />}
        </>
      )}
    </Box>
  );
}
