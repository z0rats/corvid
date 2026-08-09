import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import SearchForm from './SearchForm';
import LiveScanView from './LiveScanView';
import HudsonRockSection from './HudsonRockSection';
import ToolInfoBanner from './ToolInfoBanner';
import { useUsernameSearchScan } from '../hooks/useUsernameSearchScan';
import { useHudsonRockCheck } from '../hooks/api/useHudsonRockCheck';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';

export default function NewSearch() {
  const { t } = useTranslation('usernameSearch');
  const maigretScan = useUsernameSearchScan('maigret');
  const socialAnalyzerScan = useUsernameSearchScan('social_analyzer');
  const threatActorScan = useUsernameSearchScan('threat_actor_usernames');
  const [hudsonRockUsername, setHudsonRockUsername] = useState(null);
  const hudsonRockResult = useHudsonRockCheck(hudsonRockUsername);

  const scansByModule = {
    maigret: maigretScan,
    social_analyzer: socialAnalyzerScan,
    threat_actor_usernames: threatActorScan,
  };
  const anyScanRunning = Object.values(scansByModule).some((scan) => scan.phase === 'running');

  const handleSearch = (username, { modules, tags }) => {
    modules.forEach((moduleKey) => {
      if (moduleKey === 'hudson_rock') {
        setHudsonRockUsername(username);
      } else {
        scansByModule[moduleKey].startScan(username, { tags });
      }
    });
  };

  // Hand-off from a command-palette pivot (e.g. "john_doe username") — see crossFeatureNav.js.
  // Deliberately only starts Maigret, not every module, so a quick pivot click doesn't surprise
  // the user with several parallel scans.
  const prefillValue = usePrefillFromQuery(useCallback((value) => maigretScan.startScan(value), [maigretScan]));

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 1 }}>{t('page.title')}</Typography>
      <ToolInfoBanner />
      <SearchForm onSearch={handleSearch} disabled={anyScanRunning} initialUsername={prefillValue} />
      {maigretScan.phase !== 'idle' && <LiveScanView scan={maigretScan} title={t('form.sourceMaigret')} />}
      {socialAnalyzerScan.phase !== 'idle' && <LiveScanView scan={socialAnalyzerScan} title={t('form.sourceSocialAnalyzer')} />}
      {threatActorScan.phase !== 'idle' && <LiveScanView scan={threatActorScan} title={t('form.sourceThreatActorUsernames')} />}
      {hudsonRockUsername && <HudsonRockSection result={hudsonRockResult} />}
    </Box>
  );
}
