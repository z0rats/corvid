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

  // Tracks panel display order: whichever module(s) were most recently launched move to the
  // front, so a scan started after earlier ones already have results appears above them
  // instead of always rendering in the fixed maigret/social_analyzer/threat_actor order.
  const [sourceOrder, setSourceOrder] = useState([
    'maigret', 'social_analyzer', 'threat_actor_usernames', 'hudson_rock',
  ]);
  const bringToFront = useCallback((keys) => {
    setSourceOrder((prev) => [...keys, ...prev.filter((key) => !keys.includes(key))]);
  }, []);

  const handleSearch = (username, { modules, tags }) => {
    bringToFront(modules);
    modules.forEach((moduleKey) => {
      if (moduleKey === 'hudson_rock') {
        setHudsonRockUsername(username);
      } else {
        scansByModule[moduleKey].startScan(username, { tags });
      }
    });
  };

  // Hand-off from a command-palette pivot (e.g. "john_doe username") — see crossFeatureNav.ts.
  // Deliberately only starts Maigret, not every module, so a quick pivot click doesn't surprise
  // the user with several parallel scans.
  const prefillValue = usePrefillFromQuery(useCallback((value) => {
    bringToFront(['maigret']);
    maigretScan.startScan(value);
  }, [maigretScan, bringToFront]));

  const panelsBySource = {
    maigret: () => maigretScan.phase !== 'idle'
      && <LiveScanView key="maigret" scan={maigretScan} title={t('form.sourceMaigret')} />,
    social_analyzer: () => socialAnalyzerScan.phase !== 'idle'
      && <LiveScanView key="social_analyzer" scan={socialAnalyzerScan} title={t('form.sourceSocialAnalyzer')} />,
    threat_actor_usernames: () => threatActorScan.phase !== 'idle'
      && <LiveScanView key="threat_actor_usernames" scan={threatActorScan} title={t('form.sourceThreatActorUsernames')} />,
    hudson_rock: () => hudsonRockUsername && <HudsonRockSection key="hudson_rock" result={hudsonRockResult} />,
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 1 }}>{t('page.title')}</Typography>
      <ToolInfoBanner />
      <SearchForm onSearch={handleSearch} disabled={anyScanRunning} initialUsername={prefillValue} />
      {sourceOrder.map((key) => panelsBySource[key]())}
    </Box>
  );
}
